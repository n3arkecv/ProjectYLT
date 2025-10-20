"""
情境上下文管理器
管理對話歷史和情境摘要
"""

from typing import List, Optional, Tuple
from collections import deque
from utils.logger import logger


class ContextManager:
    """情境上下文管理器"""
    
    def __init__(
        self,
        window_size: int = 5,
        update_interval: int = 3,
        max_context_length: int = 200
    ):
        """
        初始化上下文管理器
        
        Args:
            window_size: 滾動視窗大小（保留最近N句）
            update_interval: 更新摘要的間隔（每N句更新一次）
            max_context_length: 摘要最大長度（字符數）
        """
        self.window_size = window_size
        self.update_interval = update_interval
        self.max_context_length = max_context_length
        
        # 使用deque維護滾動視窗
        self.history: deque = deque(maxlen=window_size)
        self.context_summary = ""
        self.sentence_count = 0
        
        # LLM引用（用於生成摘要）
        self.llm = None
        
        logger.info(f"上下文管理器初始化: 視窗大小={window_size}, 更新間隔={update_interval}")
    
    def set_llm(self, llm) -> None:
        """
        設置LLM引用（用於生成摘要）
        
        Args:
            llm: LLM模塊實例
        """
        self.llm = llm
    
    def add_sentence(self, original: str, translation: str = "") -> None:
        """
        添加新句子到歷史
        
        Args:
            original: 原文
            translation: 譯文
        """
        if not original.strip():
            return
        
        self.history.append({
            "original": original.strip(),
            "translation": translation.strip()
        })
        self.sentence_count += 1
        
        logger.debug(f"添加句子到上下文: {original[:20]}...")
        
        # 檢查是否需要更新摘要
        if self.sentence_count % self.update_interval == 0:
            self._update_summary()
    
    def get_context_summary(self) -> str:
        """
        獲取當前情境摘要
        
        Returns:
            格式化的情境摘要
        """
        # 如果沒有摘要，返回最近的對話
        if not self.context_summary:
            return self._get_recent_context()
        
        # 返回摘要 + 最近對話
        recent = self._get_recent_context()
        if recent:
            return f"情境: {self.context_summary}\n\n{recent}"
        else:
            return f"情境: {self.context_summary}"
    
    def _get_recent_context(self, num_sentences: int = 2) -> str:
        """
        獲取最近的對話
        
        Args:
            num_sentences: 獲取最近N句
            
        Returns:
            格式化的最近對話
        """
        if not self.history:
            return ""
        
        recent_sentences = list(self.history)[-num_sentences:]
        
        if not recent_sentences:
            return ""
        
        lines = ["最近對話:"]
        for item in recent_sentences:
            lines.append(f"- {item['original']}")
        
        return "\n".join(lines)
    
    def _update_summary(self) -> None:
        """更新情境摘要（使用LLM）"""
        if not self.llm or len(self.history) < 2:
            return
        
        try:
            logger.debug("正在更新情境摘要...")
            
            # 構建歷史文本
            history_text = "\n".join([
                f"{i+1}. {item['original']}"
                for i, item in enumerate(self.history)
            ])
            
            # 使用LLM生成簡短摘要
            prompt = f"""請用1-2句話（不超過{self.max_context_length}字）總結以下對話的主題和情境：

{history_text}

摘要："""
            
            summary = self.llm.generate_summary(prompt)
            
            if summary:
                self.context_summary = summary[:self.max_context_length]
                logger.info(f"情境摘要已更新: {self.context_summary}")
        
        except Exception as e:
            logger.error(f"更新情境摘要時發生錯誤: {e}")
    
    def get_translation_context(self) -> str:
        """
        獲取用於翻譯的上下文
        
        Returns:
            格式化的翻譯上下文
        """
        context = self.get_context_summary()
        
        if not context:
            return ""
        
        return f"\n參考上下文：\n{context}\n"
    
    def clear(self) -> None:
        """清空所有上下文"""
        self.history.clear()
        self.context_summary = ""
        self.sentence_count = 0
        logger.info("上下文已清空")
    
    def get_history_list(self) -> List[dict]:
        """
        獲取歷史記錄列表
        
        Returns:
            歷史記錄列表
        """
        return list(self.history)
    
    def export_context(self) -> dict:
        """
        導出上下文狀態
        
        Returns:
            上下文狀態字典
        """
        return {
            "history": list(self.history),
            "summary": self.context_summary,
            "sentence_count": self.sentence_count
        }
    
    def import_context(self, context_data: dict) -> None:
        """
        導入上下文狀態
        
        Args:
            context_data: 上下文狀態字典
        """
        try:
            self.history.clear()
            for item in context_data.get("history", []):
                self.history.append(item)
            
            self.context_summary = context_data.get("summary", "")
            self.sentence_count = context_data.get("sentence_count", 0)
            
            logger.info("上下文已導入")
        except Exception as e:
            logger.error(f"導入上下文時發生錯誤: {e}")


class SimpleContextManager(ContextManager):
    """簡化版上下文管理器（不使用LLM生成摘要）"""
    
    def _update_summary(self) -> None:
        """簡單更新摘要（不使用LLM）"""
        if len(self.history) < 2:
            return
        
        # 只保留最近幾句的簡要描述
        recent = list(self.history)[-3:]
        summary_parts = [item['original'][:30] + "..." for item in recent]
        self.context_summary = " → ".join(summary_parts)
        
        # 確保不超過最大長度
        if len(self.context_summary) > self.max_context_length:
            self.context_summary = self.context_summary[:self.max_context_length] + "..."
        
        logger.debug(f"簡化摘要已更新: {self.context_summary}")

