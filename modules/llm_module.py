"""
LLM模塊
直接載入並使用LLM模型進行翻譯
"""

import sys
import threading
import queue
import traceback
from typing import Optional, Callable
from pathlib import Path
from utils.logger import logger


def _load_model(model_path: str, n_gpu_layers: int, n_ctx: int):
    """載入LLM模型（內部函數）"""
    try:
        from llama_cpp import Llama
        
        logger.info(f"載入模型: {model_path}")
        
        model = Llama(
            model_path=model_path,
            n_gpu_layers=n_gpu_layers,
            n_ctx=n_ctx,
            n_batch=512,
            verbose=False
        )
        
        # 簡單測試 - 確保模型可以正常使用
        try:
            response = model.create_completion(
                prompt="Hello",
                max_tokens=10,
                temperature=0.3,
                echo=False
            )
            logger.info("模型載入成功")
        except Exception as e:
            logger.error(f"模型載入後測試失敗: {e}")
            raise e
        
        return model
            
    except Exception as e:
        logger.error(f"載入模型時發生錯誤: {e}")
        traceback.print_exc(file=sys.stderr)
        return None


class LLMModule:
    """LLM模塊（直接載入）"""
    
    def __init__(
        self,
        model_path: str = "models/qwen2.5-7b-instruct-q4_k_m.gguf",
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
        
        self.model = None
        self.is_ready = False
        
        logger.info(f"LLM模塊初始化: model={model_path}, n_gpu_layers={n_gpu_layers}")
    
    def load_model(self) -> bool:
        """
        載入LLM模型
        
        Returns:
            是否載入成功
        """
        try:
            logger.info("正在載入LLM模型...")
            
            self.model = _load_model(self.model_path, self.n_gpu_layers, self.n_ctx)
            
            if self.model:
                self.is_ready = True
                logger.info("LLM模型載入完成")
                return True
            else:
                logger.error("LLM模型載入失敗")
                return False
                
        except Exception as e:
            logger.error(f"載入LLM模型時發生錯誤: {e}")
            return False
    
    def warm_up(self) -> None:
        """預熱模型"""
        if not self.is_ready or not self.model:
            logger.warning("模型未載入，無法預熱")
            return
        
        try:
            logger.info("預熱LLM模型...")
            
            response = self.model.create_completion(
                prompt="測試翻譯功能",
                max_tokens=10,
                temperature=0.3,
                echo=False
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                translation = response.choices[0].text.strip()
            else:
                translation = str(response).strip()
            
            logger.info(f"LLM模型預熱完成: {translation}")
                
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
            streaming: 是否使用串流輸出（暫不支援）
            
        Returns:
            翻譯結果
        """
        if not self.is_ready or not self.model:
            logger.error("模型未載入，無法翻譯")
            return ""
        
        if not japanese_text.strip():
            return ""
        
        try:
            # 構建提示詞
            prompt = f"請將以下日文翻譯成繁體中文：{japanese_text}"
            if context:
                prompt = f"上下文：{context}\n{prompt}"
            
            # 執行翻譯
            response = self.model.create_completion(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=self.temperature,
                echo=False
            )
            
            # 提取翻譯結果
            if hasattr(response, 'choices') and len(response.choices) > 0:
                translation = response.choices[0].text.strip()
            else:
                # 嘗試不同的響應格式
                translation = str(response).strip()
            
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
        串流式翻譯（暫不支援，回退到普通翻譯）
        
        Args:
            japanese_text: 日文原文
            context: 上下文信息
            callback: 每個token的回調函數
            
        Returns:
            完整翻譯結果
        """
        # 回退到普通翻譯
        translation = self.translate(japanese_text, context)
        
        # 模擬串流效果
        if callback and translation:
            for char in translation:
                callback(char)
        
        return translation
    
    def generate_summary(self, prompt: str, max_tokens: int = 150) -> str:
        """
        生成摘要
        
        Args:
            prompt: 提示詞
            max_tokens: 最大tokens
            
        Returns:
            生成的摘要
        """
        if not self.is_ready or not self.model:
            return ""
        
        try:
            response = self.model.create_completion(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=self.temperature,
                echo=False
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].text.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            logger.error(f"生成摘要時發生錯誤: {e}")
            return ""


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


def main():
    """主函數（命令行界面）"""
    if len(sys.argv) < 2:
        print("用法: python llm_module.py <command> [args...]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # 載入配置
    from utils.config import config
    
    model_path = config.get("models.llm_model", "models/qwen2.5-7b-instruct-q4_k_m.gguf")
    n_gpu_layers = config.get("models.llm_n_gpu_layers", 35)
    n_ctx = config.get("models.llm_n_ctx", 2048)
    
    if command == "load":
        # 載入模型
        model = _load_model(model_path, n_gpu_layers, n_ctx)
        if model:
            print("OK")
        else:
            print("ERROR")
            sys.exit(1)
    
    elif command == "translate":
        # 翻譯文本
        if len(sys.argv) < 3:
            print("ERROR: 缺少翻譯文本")
            sys.exit(1)
        
        text = sys.argv[2]
        context = sys.argv[3] if len(sys.argv) > 3 else ""
        
        model = _load_model(model_path, n_gpu_layers, n_ctx)
        if not model:
            print("ERROR: 模型載入失敗")
            sys.exit(1)
        
        try:
            # 使用正確的Llama模型API進行翻譯
            prompt = f"請將以下日文翻譯成繁體中文：{text}"
            if context:
                prompt = f"上下文：{context}\n{prompt}"

            response = model.create_completion(
                prompt=prompt,
                max_tokens=200,
                temperature=0.3,
                echo=False
            )

            # 提取翻譯結果
            if hasattr(response, 'choices') and len(response.choices) > 0:
                translation = response.choices[0].text.strip()
            else:
                # 嘗試不同的響應格式
                translation = str(response).strip()

            print(translation)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)
    
    elif command == "test":
        # 測試模型
        model = _load_model(model_path, n_gpu_layers, n_ctx)
        if not model:
            print("ERROR: 模型載入失敗")
            sys.exit(1)
        
        try:
            response = model.create_completion(
                prompt="測試翻譯功能",
                max_tokens=10,
                temperature=0.3,
                echo=False
            )
            if hasattr(response, 'choices') and len(response.choices) > 0:
                translation = response.choices[0].text.strip()
            else:
                translation = str(response).strip()
            print(f"測試成功: {translation}")
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)
    
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
