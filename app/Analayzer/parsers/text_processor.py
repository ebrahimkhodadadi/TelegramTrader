"""Text processing and normalization utilities for signal analysis"""

import unicodedata
import re


class TextProcessor:
    """Handles text cleaning and normalization for trading signal messages"""

    @staticmethod
    def clean_text(text):
        """Normalize text by removing special Unicode formatting, keeping Persian and new lines."""
        if not text:
            return ""

        # 1) حذف کامل سوپرسکریپت‌ها و ساب‌اسکریپت‌ها قبل از NFKC
        text = re.sub(r'[\u2070-\u209F]', '', text)

        # 2) حالا نرمال‌سازی بدون اینکه چیزی تبدیل به عدد بشه
        text = unicodedata.normalize("NFKC", text)

        # Remove excessive spaces but keep new lines
        text = re.sub(r'[^\S\r\n]+', ' ', text)

        # Remove specific symbols
        text = re.sub(r'[☑️❌]', '', text)

        # Remove unwanted characters but keep Persian, numbers, and common punctuation
        text = re.sub(r'[^\w\s.,:;!?(){}\[\]/\-+=@#%&*\'\"<>آ-ی]', '', text)

        return text.strip()

    @staticmethod
    def normalize_for_parsing(text):
        """Prepare text for parsing by cleaning and lowercasing"""
        if not text:
            return ""

        text = TextProcessor.clean_text(text)
        return text.lower()