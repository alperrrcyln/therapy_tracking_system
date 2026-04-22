"""
Face Detector
MediaPipe ile yuz tespiti
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, List, Tuple

from utils.logger import setup_logger

logger = setup_logger(__name__)


class FaceDetector:
    """MediaPipe ile yuz tespiti"""
    
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0,  # 0: kisa mesafe (2m), 1: uzun mesafe
            min_detection_confidence=0.5
        )
        logger.info("FaceDetector initialized")
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Frame'de yuzleri tespit et
        
        Args:
            frame: OpenCV BGR frame
        
        Returns:
            List of (x, y, width, height) tuples
        """
        try:
            # BGR -> RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Yuz tespiti
            results = self.face_detection.process(rgb_frame)
            
            faces = []
            
            if results.detections:
                h, w, _ = frame.shape
                
                for detection in results.detections:
                    # Bounding box al
                    bbox = detection.location_data.relative_bounding_box
                    
                    # Normalize edilmis koordinatlari pixel'e cevir
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # Sinirlari kontrol et
                    x = max(0, x)
                    y = max(0, y)
                    width = min(width, w - x)
                    height = min(height, h - y)
                    
                    faces.append((x, y, width, height))
            
            return faces
            
        except Exception as e:
            logger.error(f"Yuz tespiti hatasi: {e}")
            return []
    
    def draw_faces(self, frame: np.ndarray, faces: List[Tuple[int, int, int, int]]) -> np.ndarray:
        """
        Tespit edilen yuzleri frame uzerine ciz
        
        Args:
            frame: OpenCV frame
            faces: List of (x, y, w, h)
        
        Returns:
            Cizilmis frame
        """
        for (x, y, w, h) in faces:
            # Yesil dikdortgen ciz
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # "Face" etiketi ekle
            cv2.putText(
                frame,
                "Face",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
        
        return frame
    
    def extract_face_region(self, frame: np.ndarray, face: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Yuz bolgesini crop et
        
        Args:
            frame: OpenCV frame
            face: (x, y, w, h)
        
        Returns:
            Croplanmis yuz bolgesi veya None
        """
        try:
            x, y, w, h = face
            
            if w > 0 and h > 0:
                face_region = frame[y:y+h, x:x+w]
                return face_region
            
            return None
            
        except Exception as e:
            logger.error(f"Face region extract hatasi: {e}")
            return None
    
    def close(self):
        """Kaynaklari serbest birak"""
        if self.face_detection:
            self.face_detection.close()
        logger.info("FaceDetector closed")