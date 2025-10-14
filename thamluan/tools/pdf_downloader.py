"""
PDF Downloader - Download PDFs với deduplication (hash-based)
"""

import requests
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import json
from datetime import datetime

from core.config import config
from core.types import ToolResult

logger = logging.getLogger(__name__)


class PDFDownloader:
    """
    Download PDFs với tính năng:
    - Hash-based deduplication
    - Metadata tracking
    - Resume download support
    - Validation
    """
    
    def __init__(self):
        self.pdf_dir = config.PDF_DIR
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file để track downloaded PDFs
        self.metadata_file = self.pdf_dir / 'pdf_metadata.json'
        self.metadata = self._load_metadata()
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.USER_AGENT})
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata của PDFs đã download"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading metadata: {str(e)}")
        return {}
    
    def _save_metadata(self):
        """Save metadata ra file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
    
    def calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash của file"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def check_duplicate(self, url: str, doc_id: str) -> Optional[str]:
        """
        Kiểm tra PDF đã download chưa
        
        Returns:
            Path to existing PDF nếu đã có, None nếu chưa
        """
        # Check by doc_id
        if doc_id in self.metadata:
            pdf_path = Path(self.metadata[doc_id]['path'])
            if pdf_path.exists():
                logger.info(f"✓ PDF already exists (doc_id): {doc_id}")
                return str(pdf_path)
        
        # Check by URL
        for stored_id, info in self.metadata.items():
            if info.get('url') == url:
                pdf_path = Path(info['path'])
                if pdf_path.exists():
                    logger.info(f"✓ PDF already exists (URL): {url}")
                    return str(pdf_path)
        
        return None
    
    def download_pdf(
        self,
        url: str,
        doc_id: str,
        filename: Optional[str] = None,
        force: bool = False
    ) -> ToolResult:
        """
        Download PDF với deduplication
        
        Args:
            url: URL của PDF
            doc_id: Unique document ID
            filename: Custom filename (optional)
            force: Force download ngay cả khi đã có
            
        Returns:
            ToolResult với PDF path và metadata
        """
        try:
            # Check duplicate nếu không force
            if not force:
                existing_path = self.check_duplicate(url, doc_id)
                if existing_path:
                    return ToolResult(
                        success=True,
                        data={
                            'path': existing_path,
                            'doc_id': doc_id,
                            'is_cached': True,
                            'metadata': self.metadata.get(doc_id, {})
                        }
                    )
            
            logger.info(f"Downloading PDF: {url}")
            
            # Generate filename
            if not filename:
                # Extract from URL or use doc_id
                url_parts = url.split('/')
                filename = url_parts[-1] if url_parts[-1].endswith('.pdf') else f"{doc_id}.pdf"
            
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            pdf_path = self.pdf_dir / filename
            
            # Download
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Validate content type
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                logger.warning(f"Content-Type may not be PDF: {content_type}")
            
            # Save PDF
            total_size = 0
            with open(pdf_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            # Validate file size
            if total_size < 1024:  # Less than 1KB - suspicious
                pdf_path.unlink()
                return ToolResult(
                    success=False,
                    error=f"Downloaded file too small ({total_size} bytes), likely not a valid PDF"
                )
            
            # Calculate hash
            file_hash = self.calculate_hash(pdf_path)
            
            # Check if same hash exists (same content, different URL)
            for stored_id, info in self.metadata.items():
                if info.get('hash') == file_hash and stored_id != doc_id:
                    logger.info(f"PDF with same hash already exists: {stored_id}")
                    # Optionally, could delete new file and use existing
                    # For now, keep both
            
            # Store metadata
            self.metadata[doc_id] = {
                'url': url,
                'path': str(pdf_path),
                'filename': filename,
                'hash': file_hash,
                'size': total_size,
                'downloaded_at': datetime.now().isoformat()
            }
            self._save_metadata()
            
            logger.info(f"✅ Downloaded: {filename} ({total_size:,} bytes)")
            
            return ToolResult(
                success=True,
                data={
                    'path': str(pdf_path),
                    'doc_id': doc_id,
                    'filename': filename,
                    'hash': file_hash,
                    'size': total_size,
                    'is_cached': False
                }
            )
            
        except Exception as e:
            logger.error(f"PDF download error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to download PDF: {str(e)}"
            )
    
    def download_multiple_pdfs(
        self,
        documents: list,
        max_downloads: int = 10
    ) -> ToolResult:
        """
        Download multiple PDFs
        
        Args:
            documents: List of DocumentCard hoặc dicts với 'pdf_url' và 'doc_id'
            max_downloads: Max số PDFs để download
            
        Returns:
            ToolResult với list downloaded PDFs
        """
        try:
            downloaded = []
            failed = []
            cached = []
            
            for i, doc in enumerate(documents[:max_downloads], 1):
                # Get URL và doc_id
                if hasattr(doc, 'pdf_url'):
                    url = doc.pdf_url
                    doc_id = doc.doc_id
                else:
                    url = doc.get('pdf_url')
                    doc_id = doc.get('doc_id')
                
                if not url:
                    logger.warning(f"Document {doc_id} has no PDF URL")
                    continue
                
                logger.info(f"Downloading {i}/{min(len(documents), max_downloads)}: {doc_id}")
                
                result = self.download_pdf(url, doc_id)
                
                if result.success:
                    if result.data.get('is_cached'):
                        cached.append(result.data)
                    else:
                        downloaded.append(result.data)
                else:
                    failed.append({
                        'doc_id': doc_id,
                        'url': url,
                        'error': result.error
                    })
            
            logger.info(f"✅ Downloaded: {len(downloaded)} | Cached: {len(cached)} | Failed: {len(failed)}")
            
            return ToolResult(
                success=True,
                data={
                    'downloaded': downloaded,
                    'cached': cached,
                    'failed': failed,
                    'total': len(downloaded) + len(cached)
                }
            )
            
        except Exception as e:
            logger.error(f"Multiple PDF download error: {str(e)}")
            return ToolResult(
                success=False,
                error=f"Failed to download PDFs: {str(e)}"
            )
    
    def get_pdf_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata của PDF đã download"""
        return self.metadata.get(doc_id)
    
    def list_downloaded_pdfs(self) -> list:
        """List tất cả PDFs đã download"""
        return list(self.metadata.values())
    
    def cleanup_orphaned_files(self) -> int:
        """Remove PDFs không có trong metadata"""
        removed = 0
        tracked_files = {Path(info['path']) for info in self.metadata.values()}
        
        for pdf_file in self.pdf_dir.glob('*.pdf'):
            if pdf_file not in tracked_files:
                logger.info(f"Removing orphaned file: {pdf_file.name}")
                pdf_file.unlink()
                removed += 1
        
        return removed


# Singleton instance
pdf_downloader = PDFDownloader()
