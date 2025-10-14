"""
NLP Analyzer - Phân tích NLP đầy đủ với Sentiment + Stance + Topics
"""

import logging
from typing import List, Dict, Any, Optional
from textblob import TextBlob
import re
from collections import Counter
from datetime import datetime

from core.config import config
from core.types import ToolResult

logger = logging.getLogger(__name__)


class NLPAnalyzer:
    """
    NLP Analyzer với các tính năng:
    - Sentiment analysis (positive/negative/neutral)
    - Stance detection (support/oppose/neutral)
    - Topic extraction
    - Entity recognition
    - Text normalization
    """
    
    def __init__(self):
        self.stopwords = config.VIETNAMESE_STOPWORDS
        
        # Stance detection keywords
        self.support_keywords = [
            'đồng ý', 'ủng hộ', 'tán thành', 'đúng đắn', 'hợp lý',
            'tích cực', 'cần thiết', 'quan trọng', 'tốt', 'hay',
            'nên', 'khẳng định', 'đồng tình', 'chấp nhận'
        ]
        
        self.oppose_keywords = [
            'phản đối', 'không đồng ý', 'bất hợp lý', 'sai lầm', 'không nên',
            'tiêu cực', 'không cần thiết', 'không tốt', 'tệ', 'dở',
            'chống', 'từ chối', 'bác bỏ', 'nghi ngờ', 'lo ngại'
        ]
        
        # Topic keywords for law-related content
        self.topic_categories = {
            'quy_định': ['quy định', 'điều khoản', 'điều', 'khoản', 'chương', 'mục'],
            'quyền_lợi': ['quyền', 'lợi ích', 'quyền lợi', 'quyền hạn', 'nghĩa vụ'],
            'trách_nhiệm': ['trách nhiệm', 'nghĩa vụ', 'chế재', 'xử phạt', 'vi phạm'],
            'thủ_tục': ['thủ tục', 'hồ sơ', 'giấy tờ', 'đăng ký', 'cấp phép'],
            'tài_chính': ['thuế', 'phí', 'lệ phí', 'ngân sách', 'tài chính', 'kinh phí'],
            'tổ_chức': ['tổ chức', 'cơ quan', 'bộ', 'ủy ban', 'hội đồng'],
        }
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Phân tích cảm xúc của text
        
        Returns:
            'positive' | 'negative' | 'neutral'
        """
        try:
            # Normalize text
            text_clean = self._normalize_text(text)
            
            # Use TextBlob for sentiment
            blob = TextBlob(text_clean)
            polarity = blob.sentiment.polarity
            
            # Classify
            if polarity > 0.1:
                return 'positive'
            elif polarity < -0.1:
                return 'negative'
            else:
                return 'neutral'
                
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return 'neutral'
    
    def detect_stance(self, text: str, topic: str = "") -> Dict[str, Any]:
        """
        Phát hiện lập trường (stance) về một chủ đề
        
        Returns:
            {
                'stance': 'support' | 'oppose' | 'neutral',
                'confidence': float (0-1),
                'support_score': float,
                'oppose_score': float,
                'reasoning': str
            }
        """
        try:
            text_lower = text.lower()
            
            # Count keyword matches
            support_score = sum(1 for kw in self.support_keywords if kw in text_lower)
            oppose_score = sum(1 for kw in self.oppose_keywords if kw in text_lower)
            
            # Normalize scores
            total_keywords = len(text_lower.split())
            support_ratio = support_score / max(total_keywords / 100, 1)
            oppose_ratio = oppose_score / max(total_keywords / 100, 1)
            
            # Determine stance
            if support_ratio > oppose_ratio and support_ratio > 0.5:
                stance = 'support'
                confidence = min(support_ratio / (support_ratio + oppose_ratio + 0.1), 0.95)
            elif oppose_ratio > support_ratio and oppose_ratio > 0.5:
                stance = 'oppose'
                confidence = min(oppose_ratio / (support_ratio + oppose_ratio + 0.1), 0.95)
            else:
                stance = 'neutral'
                confidence = 0.6
            
            # Generate reasoning
            reasoning = self._generate_stance_reasoning(
                stance, support_score, oppose_score
            )
            
            return {
                'stance': stance,
                'confidence': confidence,
                'support_score': support_score,
                'oppose_score': oppose_score,
                'reasoning': reasoning
            }
            
        except Exception as e:
            logger.error(f"Stance detection error: {str(e)}")
            return {
                'stance': 'neutral',
                'confidence': 0.5,
                'support_score': 0,
                'oppose_score': 0,
                'reasoning': 'Error in analysis'
            }
    
    def extract_topics(self, text: str, max_topics: int = 5) -> List[Dict[str, Any]]:
        """
        Trích xuất chủ đề từ text
        
        Returns:
            List of topics with scores
        """
        try:
            text_lower = text.lower()
            
            topic_scores = {}
            
            # Score topics based on keyword matching
            for category, keywords in self.topic_categories.items():
                score = sum(1 for kw in keywords if kw in text_lower)
                if score > 0:
                    topic_scores[category] = score
            
            # Sort by score
            sorted_topics = sorted(
                topic_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:max_topics]
            
            topics = [
                {
                    'topic': topic,
                    'score': score,
                    'label': self._get_topic_label(topic)
                }
                for topic, score in sorted_topics
            ]
            
            return topics
            
        except Exception as e:
            logger.error(f"Topic extraction error: {str(e)}")
            return []
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Trích xuất entities (tổ chức, luật, số liệu)
        
        Returns:
            {
                'organizations': [...],
                'laws': [...],
                'numbers': [...]
            }
        """
        try:
            entities = {
                'organizations': [],
                'laws': [],
                'numbers': []
            }
            
            # Extract organizations (Bộ, Ủy ban, etc.)
            org_pattern = r'(?:Bộ|Cục|Vụ|Sở|Ban|Ủy ban)\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zA-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]+'
            orgs = re.findall(org_pattern, text)
            entities['organizations'] = list(set(orgs))[:10]
            
            # Extract laws (Luật, Nghị định, etc.)
            law_pattern = r'(?:Luật|Nghị định|Thông tư|Quyết định)\s+[A-ZÀ-Ỹ][a-zà-ỹ\s,]+(?:\d{4})?'
            laws = re.findall(law_pattern, text)
            entities['laws'] = list(set(laws))[:10]
            
            # Extract important numbers (dates, percentages, amounts)
            number_pattern = r'\d+(?:[.,]\d+)?(?:\s*%|\s*tỷ|\s*triệu|\s*nghìn|\s*đồng)?'
            numbers = re.findall(number_pattern, text)
            entities['numbers'] = numbers[:20]
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction error: {str(e)}")
            return {'organizations': [], 'laws': [], 'numbers': []}
    
    def analyze_full(
        self,
        text: str,
        topic: str = "",
        include_entities: bool = True
    ) -> Dict[str, Any]:
        """
        Phân tích NLP đầy đủ
        
        Returns:
            {
                'sentiment': str,
                'stance': dict,
                'topics': list,
                'entities': dict (optional),
                'normalized_text': str,
                'stats': dict
            }
        """
        try:
            logger.info(f"Performing full NLP analysis ({len(text)} chars)")
            
            # Normalize text
            normalized = self._normalize_text(text)
            
            # Sentiment
            sentiment = self.analyze_sentiment(text)
            
            # Stance
            stance = self.detect_stance(text, topic)
            
            # Topics
            topics = self.extract_topics(text)
            
            # Entities (optional, expensive)
            entities = {}
            if include_entities:
                entities = self.extract_entities(text)
            
            # Text statistics
            stats = self._calculate_stats(text)
            
            result = {
                'sentiment': sentiment,
                'stance': stance,
                'topics': topics,
                'entities': entities,
                'normalized_text': normalized[:500],  # First 500 chars
                'stats': stats,
                'analyzed_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ NLP analysis complete: sentiment={sentiment}, stance={stance['stance']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Full NLP analysis error: {str(e)}")
            return {
                'sentiment': 'neutral',
                'stance': {'stance': 'neutral', 'confidence': 0.5},
                'topics': [],
                'entities': {},
                'normalized_text': '',
                'stats': {},
                'error': str(e)
            }
    
    def analyze_batch(
        self,
        texts: List[str],
        topic: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Phân tích batch nhiều texts
        
        Returns:
            List of analysis results
        """
        results = []
        
        for i, text in enumerate(texts, 1):
            logger.info(f"Analyzing text {i}/{len(texts)}")
            
            result = self.analyze_full(
                text,
                topic=topic,
                include_entities=(i == 1)  # Only extract entities for first text
            )
            results.append(result)
        
        logger.info(f"✅ Batch analysis complete: {len(results)} texts")
        
        return results
    
    def _normalize_text(self, text: str) -> str:
        """Chuẩn hóa text"""
        # Lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters (giữ Vietnamese)
        text = re.sub(r'[^\w\s\u00C0-\u1EF9.,;:!?()-]', '', text)
        
        return text.strip()
    
    def _calculate_stats(self, text: str) -> Dict[str, Any]:
        """Calculate text statistics"""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        return {
            'char_count': len(text),
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0
        }
    
    def _generate_stance_reasoning(
        self,
        stance: str,
        support_score: int,
        oppose_score: int
    ) -> str:
        """Generate reasoning for stance detection"""
        if stance == 'support':
            return f"Text contains {support_score} support indicators vs {oppose_score} oppose indicators"
        elif stance == 'oppose':
            return f"Text contains {oppose_score} oppose indicators vs {support_score} support indicators"
        else:
            return f"Text is balanced with {support_score} support and {oppose_score} oppose indicators"
    
    def _get_topic_label(self, topic_key: str) -> str:
        """Get human-readable label for topic"""
        labels = {
            'quy_định': 'Quy định pháp luật',
            'quyền_lợi': 'Quyền lợi',
            'trách_nhiệm': 'Trách nhiệm',
            'thủ_tục': 'Thủ tục hành chính',
            'tài_chính': 'Tài chính',
            'tổ_chức': 'Tổ chức bộ máy'
        }
        return labels.get(topic_key, topic_key)


# Singleton instance
nlp_analyzer = NLPAnalyzer()
