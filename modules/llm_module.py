"""
LLM翻譯模塊
使用llama-cpp-python進行翻譯
"""

import threading
import queue
from typing import Optional, Callable
from pathlib import Path
from llama_cpp import Llama
from utils.logger import logger


class LLMModule:
    """LLM翻譯模塊"""
    
    def __init__(
        self,
        model_path: str,
        n_gpu_layers: int = 35,
        n_ctx: int = 2048,
        n_batch: int = 512,
        temperature: float = 0.3
    ):
        """
        初始化LLM模塊
        
        Args:
            model_path: 模型文件路徑
            n_gpu_layers: GPU層數
            n_ctx: 上下文長度
            n_batch: 批次大小
            temperature: 溫度參數
        """
        self.model_path = model_path
        self.n_gpu_layers = n_gpu_layers
        self.n_ctx = n_ctx
        self.n_batch = n_batch
        self.temperature = temperature
        
        self.model: Optional[Llama] = None
        self.is_ready = False
        
        logger.info(f"LLM模塊初始化: model={model_path}, n_gpu_layers={n_gpu_layers}")
    
    def load_model(self) -> bool:
        """
        載入LLM模型
        
        Returns:
            是否載入成功
        """
        try:
            model_file = Path(self.model_path)
            
            if not model_file.exists():
                logger.error(f"模型文件不存在: {self.model_path}")
                return False
            
            logger.info(f"正在載入LLM模型: {self.model_path}")
            
            self.model = Llama(
                model_path=self.model_path,
                n_gpu_layers=self.n_gpu_layers,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                verbose=False
            )
            
            self.is_ready = True
            logger.info("LLM模型載入完成")
            return True
            
        except Exception as e:
            logger.error(f"載入LLM模型時發生錯誤: {e}")
            self.is_ready = False
            return False
    
    def warm_up(self) -> None:
        """預熱模型"""
        if not self.is_ready:
            logger.warning("模型未載入，無法預熱")
            return
        
        try:
            logger.info("預熱LLM模型...")
            self.model(
                "こんにちは",
                max_tokens=10,
                temperature=self.temperature,
                echo=False
            )
            logger.info("LLM模型預熱完成")
        except Exception as e:
            logger.error(f"預熱LLM模型時發生錯誤: {e}")
    
    def translate(
        self,
        japanese_text: str,
        context: str = "",
        max_tokens: int = 200,
        streaming: bool = False
    ) -> str:
        """
        翻譯日文到繁體中文
        
        Args:
            japanese_text: 日文原文
            context: 上下文信息
            max_tokens: 最大生成tokens
            streaming: 是否使用串流輸出
            
        Returns:
            翻譯結果
        """
        if not self.is_ready:
            logger.error("模型未載入，無法翻譯")
            return ""
        
        if not japanese_text.strip():
            return ""
        
        try:
            # 構建prompt
            prompt = self._build_translation_prompt(japanese_text, context)
            
            # 生成翻譯
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=self.temperature,
                stop=["原文:", "\n原文", "###"],
                echo=False,
                stream=streaming
            )
            
            if streaming:
                # 串流模式
                translation = ""
                for chunk in response:
                    if 'choices' in chunk:
                        text = chunk['choices'][0].get('text', '')
                        translation += text
                return translation.strip()
            else:
                # 非串流模式
                translation = response['choices'][0]['text'].strip()
                return translation
                
        except Exception as e:
            logger.error(f"翻譯時發生錯誤: {e}")
            return ""
    
    def translate_streaming(
        self,
        japanese_text: str,
        context: str = "",
        callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        串流式翻譯（逐字輸出）
        
        Args:
            japanese_text: 日文原文
            context: 上下文信息
            callback: 每個token的回調函數
            
        Returns:
            完整翻譯結果
        """
        if not self.is_ready:
            logger.error("模型未載入，無法翻譯")
            return ""
        
        if not japanese_text.strip():
            return ""
        
        try:
            prompt = self._build_translation_prompt(japanese_text, context)
            
            response = self.model(
                prompt,
                max_tokens=200,
                temperature=self.temperature,
                stop=["原文:", "\n原文", "###"],
                echo=False,
                stream=True
            )
            
            translation = ""
            for chunk in response:
                if 'choices' in chunk:
                    text = chunk['choices'][0].get('text', '')
                    if text:
                        translation += text
                        if callback:
                            callback(text)
            
            return translation.strip()
            
        except Exception as e:
            logger.error(f"串流翻譯時發生錯誤: {e}")
            return ""
    
    def generate_summary(self, prompt: str, max_tokens: int = 150) -> str:
        """
        生成摘要
        
        Args:
            prompt: 提示詞
            max_tokens: 最大tokens
            
        Returns:
            生成的摘要
        """
        if not self.is_ready:
            return ""
        
        try:
            response = self.model(
                prompt,
                max_tokens=max_tokens,
                temperature=0.3,
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
            
        except Exception as e:
            logger.error(f"生成摘要時發生錯誤: {e}")
            return ""
    
    def _build_translation_prompt(self, japanese_text: str, context: str = "") -> str:
        """
        構建翻譯prompt
        
        Args:
            japanese_text: 日文原文
            context: 上下文
            
        Returns:
            完整的prompt
        """
        if context:
            prompt = f"""你是專業的日文翻譯。請將以下日文翻譯為繁體中文，保持自然流暢。

{context}

原文: {japanese_text}
譯文:"""
        else:
            prompt = f"""你是專業的日文翻譯。請將以下日文翻譯為繁體中文，保持自然流暢。

原文: {japanese_text}
譯文:"""
        
        return prompt


class LLMProcessor:
    """LLM處理器（異步處理）"""
    
    def __init__(self, llm_module: LLMModule, context_manager=None):
        """
        初始化LLM處理器
        
        Args:
            llm_module: LLM模塊實例
            context_manager: 上下文管理器實例
        """
        self.llm = llm_module
        self.context_manager = context_manager
        
        self.is_running = False
        self.process_thread: Optional[threading.Thread] = None
        self.text_queue = queue.Queue(maxsize=5)
        self.result_queue = queue.Queue(maxsize=10)
    
    def start(self) -> None:
        """啟動處理器"""
        if self.is_running:
            logger.warning("LLM處理器已在運行中")
            return
        
        self.is_running = True
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        logger.info("LLM處理器已啟動")
    
    def stop(self) -> None:
        """停止處理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.process_thread:
            self.process_thread.join(timeout=2.0)
        
        logger.info("LLM處理器已停止")
    
    def put_text(self, text: str) -> bool:
        """
        放入文本進行翻譯
        
        Args:
            text: 待翻譯文本
            
        Returns:
            是否成功放入
        """
        try:
            self.text_queue.put_nowait(text)
            return True
        except queue.Full:
            logger.warning("LLM文本隊列已滿，丟棄數據")
            return False
    
    def get_result(self, timeout: float = 0.1) -> Optional[dict]:
        """
        獲取翻譯結果
        
        Args:
            timeout: 超時時間
            
        Returns:
            結果字典或None
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def _process_loop(self) -> None:
        """處理循環"""
        logger.debug("LLM處理線程已啟動")
        
        while self.is_running:
            try:
                # 獲取待翻譯文本
                text = self.text_queue.get(timeout=0.5)
                
                # 獲取上下文
                context = ""
                if self.context_manager:
                    context = self.context_manager.get_translation_context()
                
                # 翻譯
                translation = self.llm.translate(text, context)
                
                if translation:
                    # 更新上下文
                    if self.context_manager:
                        self.context_manager.add_sentence(text, translation)
                    
                    result = {
                        "original": text,
                        "translation": translation,
                        "context": self.context_manager.get_context_summary() if self.context_manager else ""
                    }
                    
                    try:
                        self.result_queue.put_nowait(result)
                    except queue.Full:
                        # 移除最舊的結果
                        try:
                            self.result_queue.get_nowait()
                            self.result_queue.put_nowait(result)
                        except:
                            pass
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"LLM處理循環錯誤: {e}")
        
        logger.debug("LLM處理線程已結束")

