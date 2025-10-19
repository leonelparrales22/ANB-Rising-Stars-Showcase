import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
import uuid

# Mock de las dependencias antes de importar el módulo
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app-worker'))

with patch('shared.db.config.get_db'):
    with patch('shared.config.settings.settings'):
        with patch('shared.db.models.video.Video'):
            with patch('shared.db.models.user.User'):
                with patch('shared.db.models.vote.Vote'):
                    from worker.tasks.video_processing import (
                        process_video_task,
                        trim_video_to_30s,
                        resize_to_720p_16_9,
                        add_anb_intro_outro,
                        create_simple_intro_outro
                    )


class TestVideoProcessing:
    """Pruebas unitarias para el procesamiento de videos."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock de la sesión de base de datos."""
        mock_db = MagicMock()
        mock_video = MagicMock()
        mock_video.id = "test-video-id"
        mock_video.status = "uploaded"
        mock_video.file_original_url = "/test/path/video.mp4"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_video
        return mock_db

    @pytest.fixture
    def mock_settings(self):
        """Mock de la configuración."""
        mock_settings = MagicMock()
        mock_settings.uploads_dir = "/test/uploads"
        mock_settings.assets_dir = "/test/assets"
        return mock_settings

    @patch('worker.tasks.video_processing.subprocess.run')
    def test_trim_video_to_30s_success(self, mock_subprocess):
        """Prueba exitosa del recorte de video a 30 segundos."""
        # Configurar mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = trim_video_to_30s("/input/video.mp4", "/output/video.mp4")
        
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert '-t' in call_args
        assert '30' in call_args

    @patch('worker.tasks.video_processing.subprocess.run')
    def test_trim_video_to_30s_failure(self, mock_subprocess):
        """Prueba de fallo en el recorte de video."""
        # Configurar mock para fallo
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        result = trim_video_to_30s("/input/video.mp4", "/output/video.mp4")
        
        assert result is False

    @patch('worker.tasks.video_processing.subprocess.run')
    def test_resize_to_720p_16_9_success(self, mock_subprocess):
        """Prueba exitosa del redimensionado a 720p 16:9."""
        # Configurar mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = resize_to_720p_16_9("/input/video.mp4", "/output/video.mp4")
        
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert 'scale=1280:720' in ' '.join(call_args)

    @patch('worker.tasks.video_processing.subprocess.run')
    def test_resize_to_720p_16_9_failure(self, mock_subprocess):
        """Prueba de fallo en el redimensionado."""
        # Configurar mock para fallo
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error message"
        mock_result.stdout = "Output message"
        mock_subprocess.return_value = mock_result
        
        result = resize_to_720p_16_9("/input/video.mp4", "/output/video.mp4")
        
        assert result is False

    @patch('worker.tasks.video_processing.subprocess.run')
    @patch('app_worker.worker.tasks.video_processing.os.path.exists')
    @patch('app_worker.worker.tasks.video_processing.os.makedirs')
    def test_add_anb_intro_outro_success(self, mock_makedirs, mock_exists, mock_subprocess):
        """Prueba exitosa de agregar cortinillas ANB."""
        # Configurar mocks
        mock_exists.return_value = True  # Los archivos de intro/outro existen
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        result = add_anb_intro_outro("/input/video.mp4", "/output/video.mp4")
        
        assert result is True
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert 'ffmpeg' in call_args
        assert '-filter_complex' in call_args

    @patch('worker.tasks.video_processing.subprocess.run')
    @patch('app_worker.worker.tasks.video_processing.os.path.exists')
    @patch('app_worker.worker.tasks.video_processing.os.makedirs')
    def test_add_anb_intro_outro_missing_assets(self, mock_makedirs, mock_exists, mock_subprocess):
        """Prueba cuando faltan los archivos de intro/outro."""
        # Configurar mocks
        mock_exists.return_value = False  # Los archivos no existen
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Mock de create_simple_intro_outro
        with patch('worker.tasks.video_processing.create_simple_intro_outro') as mock_create:
            result = add_anb_intro_outro("/input/video.mp4", "/output/video.mp4")
            
            assert result is True
            mock_create.assert_called_once()

    @patch('worker.tasks.video_processing.subprocess.run')
    @patch('app_worker.worker.tasks.video_processing.os.makedirs')
    def test_create_simple_intro_outro_success(self, mock_makedirs, mock_subprocess):
        """Prueba exitosa de creación de intro/outro simples."""
        # Configurar mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        create_simple_intro_outro("/test/intro.mp4", "/test/outro.mp4")
        
        # Verificar que se llamó subprocess.run dos veces (intro y outro)
        assert mock_subprocess.call_count == 2
        mock_makedirs.assert_called_once()

    @patch('worker.tasks.video_processing.subprocess.run')
    def test_create_simple_intro_outro_failure(self, mock_subprocess):
        """Prueba de fallo en la creación de intro/outro."""
        # Configurar mock para fallo
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error message"
        mock_subprocess.return_value = mock_result
        
        # No debería lanzar excepción, solo loggear el error
        create_simple_intro_outro("/test/intro.mp4", "/test/outro.mp4")
        
        assert mock_subprocess.call_count == 2

    @patch('worker.tasks.video_processing.get_db')
    @patch('app_worker.worker.tasks.video_processing.settings')
    @patch('app_worker.worker.tasks.video_processing.os.path.exists')
    @patch('app_worker.worker.tasks.video_processing.trim_video_to_30s')
    @patch('app_worker.worker.tasks.video_processing.resize_to_720p_16_9')
    @patch('app_worker.worker.tasks.video_processing.add_anb_intro_outro')
    @patch('app_worker.worker.tasks.video_processing.os.remove')
    @patch('app_worker.worker.tasks.video_processing.os.rename')
    def test_process_video_task_success(self, mock_rename, mock_remove, mock_add_intro, 
                                       mock_resize, mock_trim, mock_exists, 
                                       mock_settings, mock_get_db, mock_db_session):
        """Prueba exitosa del procesamiento completo de video."""
        # Configurar mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        mock_settings.uploads_dir = "/test/uploads"
        mock_settings.assets_dir = "/test/assets"
        mock_exists.return_value = True
        mock_trim.return_value = True
        mock_resize.return_value = True
        mock_add_intro.return_value = True
        
        # Crear mock del task
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        
        result = process_video_task(mock_task, "test-video-id")
        
        assert result["status"] == "completed"
        assert result["video_id"] == "test-video-id"
        assert "output_path" in result
        assert "processed_at" in result

    @patch('worker.tasks.video_processing.get_db')
    def test_process_video_task_video_not_found(self, mock_get_db):
        """Prueba cuando el video no se encuentra en la base de datos."""
        # Configurar mock para video no encontrado
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value.__next__.return_value = mock_db
        
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        
        # Debería lanzar excepción
        with pytest.raises(Exception, match="Video con ID test-video-id no encontrado"):
            process_video_task(mock_task, "test-video-id")

    @patch('worker.tasks.video_processing.get_db')
    @patch('app_worker.worker.tasks.video_processing.settings')
    @patch('app_worker.worker.tasks.video_processing.os.path.exists')
    def test_process_video_task_file_not_found(self, mock_exists, mock_settings, mock_get_db, mock_db_session):
        """Prueba cuando el archivo de video no existe."""
        # Configurar mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        mock_settings.uploads_dir = "/test/uploads"
        mock_exists.return_value = False  # Archivo no existe
        
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        
        # Debería lanzar excepción
        with pytest.raises(FileNotFoundError):
            process_video_task(mock_task, "test-video-id")

    @patch('worker.tasks.video_processing.get_db')
    @patch('app_worker.worker.tasks.video_processing.settings')
    @patch('app_worker.worker.tasks.video_processing.os.path.exists')
    @patch('app_worker.worker.tasks.video_processing.trim_video_to_30s')
    def test_process_video_task_trim_failure(self, mock_trim, mock_exists, mock_settings, mock_get_db, mock_db_session):
        """Prueba cuando falla el recorte de video."""
        # Configurar mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        mock_settings.uploads_dir = "/test/uploads"
        mock_exists.return_value = True
        mock_trim.return_value = False  # Fallo en recorte
        
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        
        # Debería lanzar excepción y reintentar
        with pytest.raises(Exception):
            process_video_task(mock_task, "test-video-id")

    @patch('worker.tasks.video_processing.get_db')
    @patch('app_worker.worker.tasks.video_processing.settings')
    @patch('app_worker.worker.tasks.video_processing.os.path.exists')
    @patch('app_worker.worker.tasks.video_processing.trim_video_to_30s')
    @patch('app_worker.worker.tasks.video_processing.resize_to_720p_16_9')
    def test_process_video_task_resize_failure(self, mock_resize, mock_trim, mock_exists, mock_settings, mock_get_db, mock_db_session):
        """Prueba cuando falla el redimensionado de video."""
        # Configurar mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        mock_settings.uploads_dir = "/test/uploads"
        mock_exists.return_value = True
        mock_trim.return_value = True
        mock_resize.return_value = False  # Fallo en redimensionado
        
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        
        # Debería lanzar excepción y reintentar
        with pytest.raises(Exception):
            process_video_task(mock_task, "test-video-id")

    @patch('worker.tasks.video_processing.get_db')
    @patch('app_worker.worker.tasks.video_processing.settings')
    @patch('app_worker.worker.tasks.video_processing.os.path.exists')
    @patch('app_worker.worker.tasks.video_processing.trim_video_to_30s')
    @patch('app_worker.worker.tasks.video_processing.resize_to_720p_16_9')
    @patch('app_worker.worker.tasks.video_processing.add_anb_intro_outro')
    def test_process_video_task_intro_outro_failure(self, mock_add_intro, mock_resize, mock_trim, mock_exists, mock_settings, mock_get_db, mock_db_session):
        """Prueba cuando falla la adición de intro/outro."""
        # Configurar mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        mock_settings.uploads_dir = "/test/uploads"
        mock_exists.return_value = True
        mock_trim.return_value = True
        mock_resize.return_value = True
        mock_add_intro.return_value = False  # Fallo en intro/outro
        
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        
        # Debería lanzar excepción y reintentar
        with pytest.raises(Exception):
            process_video_task(mock_task, "test-video-id")

    @patch('worker.tasks.video_processing.get_db')
    @patch('app_worker.worker.tasks.video_processing.settings')
    @patch('app_worker.worker.tasks.video_processing.os.path.exists')
    @patch('app_worker.worker.tasks.video_processing.trim_video_to_30s')
    @patch('app_worker.worker.tasks.video_processing.resize_to_720p_16_9')
    @patch('app_worker.worker.tasks.video_processing.add_anb_intro_outro')
    @patch('app_worker.worker.tasks.video_processing.os.remove')
    @patch('app_worker.worker.tasks.video_processing.os.rename')
    def test_process_video_task_cleanup_temp_files(self, mock_rename, mock_remove, mock_add_intro, 
                                                  mock_resize, mock_trim, mock_exists, 
                                                  mock_settings, mock_get_db, mock_db_session):
        """Prueba que se limpian los archivos temporales correctamente."""
        # Configurar mocks
        mock_get_db.return_value.__next__.return_value = mock_db_session
        mock_settings.uploads_dir = "/test/uploads"
        mock_settings.assets_dir = "/test/assets"
        mock_exists.return_value = True
        mock_trim.return_value = True
        mock_resize.return_value = True
        mock_add_intro.return_value = True
        
        # Simular que existen archivos temporales para limpiar
        mock_exists.side_effect = lambda path: "temp" in path or path == "/test/path/video.mp4"
        
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        
        process_video_task(mock_task, "test-video-id")
        
        # Verificar que se llamó os.remove para limpiar archivos temporales
        assert mock_remove.call_count >= 1

    def test_process_video_task_exception_handling(self):
        """Prueba el manejo de excepciones generales."""
        mock_task = MagicMock()
        mock_task.request.id = "test-task-id"
        mock_task.retry.side_effect = Exception("Max retries exceeded")
        
        # Mock de get_db para que lance excepción
        with patch('worker.tasks.video_processing.get_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Database error")
            
            # Debería manejar la excepción y reintentar
            with pytest.raises(Exception):
                process_video_task(mock_task, "test-video-id")
