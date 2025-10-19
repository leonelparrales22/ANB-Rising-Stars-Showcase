import pytest
import subprocess
from unittest.mock import patch, MagicMock
import sys
import os

# Agregar el directorio app-worker al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app-worker'))


class TestVideoProcessingSimple:
    """Pruebas unitarias simplificadas para el procesamiento de videos."""

    @patch('subprocess.run')
    def test_trim_video_to_30s_success(self, mock_subprocess):
        """Prueba exitosa del recorte de video a 30 segundos."""
        # Configurar mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Importar la función directamente
        from worker.tasks.video_processing import trim_video_to_30s
        
        result = trim_video_to_30s("/input/video.mp4", "/output/video.mp4")
        
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert '-t' in call_args
        assert '30' in call_args

    @patch('subprocess.run')
    def test_trim_video_to_30s_failure(self, mock_subprocess):
        """Prueba de fallo en el recorte de video."""
        # Configurar mock para fallo
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        from worker.tasks.video_processing import trim_video_to_30s
        
        result = trim_video_to_30s("/input/video.mp4", "/output/video.mp4")
        
        assert result is False

    @patch('subprocess.run')
    def test_resize_to_720p_16_9_success(self, mock_subprocess):
        """Prueba exitosa del redimensionado a 720p 16:9."""
        # Configurar mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        from worker.tasks.video_processing import resize_to_720p_16_9
        
        result = resize_to_720p_16_9("/input/video.mp4", "/output/video.mp4")
        
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert 'scale=1280:720' in ' '.join(call_args)

    @patch('subprocess.run')
    def test_resize_to_720p_16_9_failure(self, mock_subprocess):
        """Prueba de fallo en el redimensionado."""
        # Configurar mock para fallo
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error message"
        mock_result.stdout = "Output message"
        mock_subprocess.return_value = mock_result
        
        from worker.tasks.video_processing import resize_to_720p_16_9
        
        result = resize_to_720p_16_9("/input/video.mp4", "/output/video.mp4")
        
        assert result is False

    @patch('subprocess.run')
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_add_anb_intro_outro_success(self, mock_makedirs, mock_exists, mock_subprocess):
        """Prueba exitosa de agregar cortinillas ANB."""
        # Configurar mocks
        mock_exists.return_value = True  # Los archivos de intro/outro existen
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        from worker.tasks.video_processing import add_anb_intro_outro
        
        result = add_anb_intro_outro("/input/video.mp4", "/output/video.mp4")
        
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert '-filter_complex' in call_args

    @patch('subprocess.run')
    @patch('os.makedirs')
    def test_create_simple_intro_outro_success(self, mock_makedirs, mock_subprocess):
        """Prueba exitosa de creación de intro/outro simples."""
        # Configurar mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        from worker.tasks.video_processing import create_simple_intro_outro
        
        create_simple_intro_outro("/test/intro.mp4", "/test/outro.mp4")
        
        # Verificar que se llamó subprocess.run dos veces (intro y outro)
        assert mock_subprocess.call_count == 2
        mock_makedirs.assert_called_once()

    @patch('subprocess.run')
    def test_create_simple_intro_outro_failure(self, mock_subprocess):
        """Prueba de fallo en la creación de intro/outro."""
        # Configurar mock para fallo
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error message"
        mock_subprocess.return_value = mock_result
        
        from worker.tasks.video_processing import create_simple_intro_outro
        
        # No debería lanzar excepción, solo loggear el error
        create_simple_intro_outro("/test/intro.mp4", "/test/outro.mp4")
        
        assert mock_subprocess.call_count == 2

    def test_video_processing_functions_exist(self):
        """Prueba que las funciones de procesamiento de video existen y son importables."""
        from worker.tasks.video_processing import (
            trim_video_to_30s,
            resize_to_720p_16_9,
            add_anb_intro_outro,
            create_simple_intro_outro
        )
        
        # Verificar que las funciones son callable
        assert callable(trim_video_to_30s)
        assert callable(resize_to_720p_16_9)
        assert callable(add_anb_intro_outro)
        assert callable(create_simple_intro_outro)

    def test_video_processing_task_exists(self):
        """Prueba que la tarea principal de procesamiento existe."""
        from worker.tasks.video_processing import process_video_task
        
        # Verificar que la función es callable
        assert callable(process_video_task)
        
        # Verificar que es una tarea de Celery
        assert hasattr(process_video_task, 'delay')
        assert hasattr(process_video_task, 'apply_async')
