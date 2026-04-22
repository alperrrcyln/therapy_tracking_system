"""
Emotion Detector
FER2013 ile egitilmis model — MediaPipe yuz tespiti + duygu analizi
"""
import cv2
import numpy as np
from typing import Optional, Dict
from tensorflow import keras
import mediapipe as mp
import os

from config import EMOTION_MODEL_PATH
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EmotionDetector:
    """Yuz algılama + duygu analizi"""

    # FER2013 egitim sirasi (degistirme)
    EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

    EMOTION_TR = {
        'angry':   'Kizgin',
        'disgust': 'Igrenmis',
        'fear':    'Korkmus',
        'happy':   'Mutlu',
        'sad':     'Uzgun',
        'surprise':'Saskin',
        'neutral': 'Notr',
    }
    EMOTION_EMOJI = {
        'angry':   '😠',
        'disgust': '🤢',
        'fear':    '😨',
        'happy':   '😊',
        'sad':     '😢',
        'surprise':'😮',
        'neutral': '😐',
    }

    def __init__(self):
        self.model = None
        self._load_model()

        _mp = mp.solutions.face_detection
        self.face_detection = _mp.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5
        )
        logger.info("EmotionDetector hazir")

    # ── Model yukleme ─────────────────────────────────────────────────────────
    def _load_model(self):
        if not os.path.exists(EMOTION_MODEL_PATH):
            logger.warning(f"Model bulunamadi: {EMOTION_MODEL_PATH}")
            return
        try:
            self.model = keras.models.load_model(
                str(EMOTION_MODEL_PATH), compile=False
            )
            logger.info("Emotion model yuklendi")
        except Exception:
            try:
                self.model = self._load_manual(str(EMOTION_MODEL_PATH))
            except Exception as e:
                logger.error(f"Model yuklenemedi: {e}")
                self.model = None

    def _load_manual(self, path: str):
        import h5py, json as _json
        with h5py.File(path, 'r') as f:
            cfg = _json.loads(f.attrs['model_config'])
        layers = cfg['config']['layers']
        input_shape = tuple(layers[0]['config']['batch_shape'][1:])
        model = keras.Sequential()
        model.add(keras.layers.Input(shape=input_shape))
        for lc in layers[1:]:
            cls  = lc['class_name']
            conf = {k: v for k, v in lc['config'].items()
                    if k not in ('name', 'trainable', 'dtype')}
            model.add(getattr(keras.layers, cls)(**conf))
        model.load_weights(path)
        logger.info("Model manuel yuklendi")
        return model

    # ── Ana metot: tam frame al, yuz bul, duygu analizi yap ──────────────────
    def detect_emotion(self, frame: np.ndarray) -> dict:
        """
        Args:
            frame: BGR OpenCV frame

        Returns:
            {
              'face_found': bool,
              'face_box':   (x, y, w, h) | None,
              'emotion':    str | None,
              'confidence': float,
              'all_predictions': {emotion: score, ...}
            }
        """
        empty = {'face_found': False, 'face_box': None,
                 'emotion': None, 'confidence': 0.0, 'all_predictions': {}}

        if self.model is None:
            return empty

        # ── Yuz tespiti ──────────────────────────────────────────────────────
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb)

        if not results.detections:
            return empty

        # En buyuk yuz
        h_frame, w_frame = frame.shape[:2]
        best = max(
            results.detections,
            key=lambda d: (d.location_data.relative_bounding_box.width *
                           d.location_data.relative_bounding_box.height)
        )
        bb = best.location_data.relative_bounding_box
        x = max(0, int(bb.xmin  * w_frame))
        y = max(0, int(bb.ymin  * h_frame))
        w = int(bb.width  * w_frame)
        h = int(bb.height * h_frame)
        x2 = min(w_frame, x + w)
        y2 = min(h_frame, y + h)

        face_roi = frame[y:y2, x:x2]
        if face_roi.size == 0 or (y2 - y) < 20 or (x2 - x) < 20:
            return empty

        # ── Preprocessing ─────────────────────────────────────────────────────
        gray    = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (48, 48), interpolation=cv2.INTER_AREA)
        # FER2013 egitim normalizasyonu: [0, 1]
        normalized = resized.astype('float32') / 255.0
        inp = normalized.reshape(1, 48, 48, 1)

        # ── Tahmin ────────────────────────────────────────────────────────────
        preds = self.model.predict(inp, verbose=0)[0]
        idx   = int(np.argmax(preds))
        if preds[idx] < 0.45:
            idx = self.EMOTIONS.index('neutral')

        all_preds = {e: float(preds[i]) for i, e in enumerate(self.EMOTIONS)}

        return {
            'face_found':      True,
            'face_box':        (x, y, w, h),
            'emotion':         self.EMOTIONS[idx],
            'confidence':      float(preds[idx]),
            'all_predictions': all_preds,
        }

    # ── Yardimci metotlar ─────────────────────────────────────────────────────
    def is_model_loaded(self) -> bool:
        return self.model is not None

    def get_emotion_turkish(self, emotion: str) -> str:
        return self.EMOTION_TR.get(emotion, emotion)

    def get_emotion_emoji(self, emotion: str) -> str:
        return self.EMOTION_EMOJI.get(emotion, '😐')

    def get_dominant_emotion(self, all_preds: dict) -> Optional[str]:
        if not all_preds:
            return None
        return max(all_preds, key=all_preds.get)

    def __del__(self):
        if hasattr(self, 'face_detection'):
            try:
                self.face_detection.close()
            except Exception:
                pass
