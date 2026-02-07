"""
Tests for the updater module
"""
import pytest
from unittest.mock import patch, MagicMock
import json

from myapp.updater import Updater, check_and_update


class TestUpdater:
    """Tests for Updater class."""
    
    def test_initialization(self):
        updater = Updater()
        assert updater.current_version is not None
        assert updater.latest_version is None
        assert updater.download_url is None
    
    @patch('myapp.updater.urllib.request.urlopen')
    def test_check_github_releases(self, mock_urlopen):
        """Test checking GitHub releases API."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'tag_name': 'v2.0.0',
            'body': 'New release',
            'assets': [
                {'name': 'myapp_2.0.0-1_all.deb', 'browser_download_url': 'https://...'}
            ]
        }).encode()
        mock_response.__enter__ = lambda s: mock_response
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        updater = Updater(use_github_releases=True)
        update_available, latest = updater.check_for_update()
        
        assert latest == '2.0.0'
        assert update_available is True
    
    @patch('myapp.updater.urllib.request.urlopen')
    def test_check_version_file(self, mock_urlopen):
        """Test checking version file URL."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'2.0.0\n'
        mock_response.__enter__ = lambda s: mock_response
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        updater = Updater(use_github_releases=False)
        update_available, latest = updater.check_for_update()
        
        assert latest == '2.0.0'
        assert update_available is True
    
    @patch('myapp.updater.urllib.request.urlopen')
    def test_no_update_available(self, mock_urlopen):
        """Test when current version matches latest."""
        from myapp import __version__
        
        mock_response = MagicMock()
        mock_response.read.return_value = f'{__version__}\n'.encode()
        mock_response.__enter__ = lambda s: mock_response
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response
        
        updater = Updater(use_github_releases=False)
        update_available, latest = updater.check_for_update()
        
        assert latest == __version__
        assert update_available is False


class TestCheckAndUpdate:
    """Tests for check_and_update function."""
    
    @patch('myapp.updater.Updater')
    def test_check_only(self, MockUpdater):
        """Test checking without installing."""
        mock_updater = MockUpdater.return_value
        mock_updater.check_for_update.return_value = (True, '2.0.0')
        mock_updater.install_update.return_value = True
        
        result = check_and_update(auto_install=False)
        
        assert result is False
        mock_updater.install_update.assert_not_called()
    
    @patch('myapp.updater.Updater')
    def test_auto_install(self, MockUpdater):
        """Test automatic installation."""
        mock_updater = MockUpdater.return_value
        mock_updater.check_for_update.return_value = (True, '2.0.0')
        mock_updater.install_update.return_value = True
        
        result = check_and_update(auto_install=True)
        
        assert result is True
        mock_updater.install_update.assert_called_once()
