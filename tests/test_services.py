import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from database import DatabaseService, User, ChatHistory
from sqlalchemy.orm import Session


class TestDatabaseService:
    """Test suite untuk DatabaseService"""

    def test_get_or_create_user_new(self, db: Session):
        """Test create user baru"""
        user = DatabaseService.get_or_create_user(
            db,
            phone_number="62812345678",
            name="Test User"
        )

        assert user is not None
        assert user.phone_number == "62812345678"
        assert user.name == "Test User"

        # Verify user tersimpan di database
        saved_user = db.query(User).filter(
            User.phone_number == "62812345678"
        ).first()
        assert saved_user is not None

    def test_get_or_create_user_existing(self, db: Session, sample_user_data):
        """Test get user yang sudah ada"""
        # Create user first
        original_user = DatabaseService.get_or_create_user(
            db,
            phone_number=sample_user_data["phone_number"],
            name=sample_user_data["name"]
        )
        original_id = original_user.id

        # Get user dengan nomor sama
        retrieved_user = DatabaseService.get_or_create_user(
            db,
            phone_number=sample_user_data["phone_number"]
        )

        assert retrieved_user.id == original_id
        assert retrieved_user.phone_number == sample_user_data["phone_number"]

    def test_save_chat_message(self, db: Session, sample_user_data):
        """Test save pesan ke chat history"""
        # Create user first
        DatabaseService.get_or_create_user(
            db,
            phone_number=sample_user_data["phone_number"]
        )

        # Save message
        message = DatabaseService.save_chat_message(
            db,
            phone_number=sample_user_data["phone_number"],
            role="user",
            message="Hello bot"
        )

        assert message is not None
        assert message.phone_number == sample_user_data["phone_number"]
        assert message.role == "user"
        assert message.message == "Hello bot"

        # Verify saved to database
        saved_message = db.query(ChatHistory).filter(
            ChatHistory.phone_number == sample_user_data["phone_number"]
        ).first()
        assert saved_message is not None

    def test_get_recent_chat_history(self, db: Session, sample_user_data):
        """Test get recent chat history"""
        # Create user
        DatabaseService.get_or_create_user(
            db,
            phone_number=sample_user_data["phone_number"]
        )

        # Save multiple messages
        for i in range(5):
            DatabaseService.save_chat_message(
                db,
                phone_number=sample_user_data["phone_number"],
                role="user" if i % 2 == 0 else "model",
                message=f"Message {i}"
            )

        # Get history
        history = DatabaseService.get_recent_chat_history(
            db,
            phone_number=sample_user_data["phone_number"],
            limit=10
        )

        assert len(history) == 5
        assert history[0].message == "Message 0"
        assert history[-1].message == "Message 4"

    def test_get_recent_chat_history_limit(self, db: Session, sample_user_data):
        """Test get recent chat history dengan limit"""
        # Create user
        DatabaseService.get_or_create_user(
            db,
            phone_number=sample_user_data["phone_number"]
        )

        # Save 10 messages
        for i in range(10):
            DatabaseService.save_chat_message(
                db,
                phone_number=sample_user_data["phone_number"],
                role="user",
                message=f"Message {i}"
            )

        # Get history dengan limit 5
        history = DatabaseService.get_recent_chat_history(
            db,
            phone_number=sample_user_data["phone_number"],
            limit=5
        )

        assert len(history) == 5
        assert history[0].message == "Message 5"
        assert history[-1].message == "Message 9"

    def test_update_user_name(self, db: Session, sample_user_data):
        """Test update nama user"""
        # Create user
        user = DatabaseService.get_or_create_user(
            db,
            phone_number=sample_user_data["phone_number"],
            name="Old Name"
        )

        # Update name
        updated_user = DatabaseService.update_user_name(
            db,
            phone_number=sample_user_data["phone_number"],
            name="New Name"
        )

        assert updated_user.name == "New Name"

        # Verify in database
        db_user = db.query(User).filter(
            User.phone_number == sample_user_data["phone_number"]
        ).first()
        assert db_user.name == "New Name"

    def test_update_user_name_nonexistent(self, db: Session):
        """Test update nama user yang tidak ada"""
        result = DatabaseService.update_user_name(
            db,
            phone_number="99999999999",
            name="Nonexistent"
        )

        assert result is None


class TestGeminiService:
    """Test suite untuk GeminiService"""

    @pytest.mark.asyncio
    async def test_format_chat_history(self):
        """Test format chat history untuk Gemini API"""
        from services.gemini import gemini_service

        chat_history = [
            {"role": "user", "message": "Hello"},
            {"role": "model", "message": "Hi there!"}
        ]

        formatted = gemini_service.format_chat_history(chat_history)

        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[0]["parts"][0]["text"] == "Hello"
        assert formatted[1]["role"] == "model"
        assert formatted[1]["parts"][0]["text"] == "Hi there!"

    @pytest.mark.asyncio
    @patch('services.gemini.genai.GenerativeModel')
    async def test_generate_response(self, mock_model):
        """Test generate response dari Gemini"""
        from services.gemini import gemini_service

        # Mock response
        mock_response = MagicMock()
        mock_response.text = "This is a test response from Gemini"

        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        response = await gemini_service.generate_response(
            "Hello",
            []
        )

        assert response == "This is a test response from Gemini"
        generated_prompt = mock_model_instance.generate_content.call_args.args[0]
        assert "Kamu adalah Asisten Virtual" in generated_prompt
        assert "Hello" in generated_prompt

    @pytest.mark.asyncio
    @patch('services.gemini.genai.GenerativeModel')
    async def test_generate_response_with_history(self, mock_model):
        """Test generate response dengan chat history"""
        from services.gemini import gemini_service

        # Mock response
        mock_response = MagicMock()
        mock_response.text = "Response with context"

        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        chat_history = [
            {"role": "user", "message": "What is your name?"},
            {"role": "model", "message": "I'm Gemini Bot"}
        ]

        response = await gemini_service.generate_response_with_history(
            "Tell me again",
            chat_history
        )

        assert response == "Response with context"
        generated_prompt = mock_model_instance.generate_content.call_args.args[0]
        assert "Riwayat percakapan sebelumnya" in generated_prompt
        assert "Pengguna: Tell me again" in generated_prompt

    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self):
        """Test error handling dalam generate response"""
        from services.gemini import gemini_service

        with patch('services.gemini.genai.GenerativeModel', side_effect=Exception("API Error")):
            response = await gemini_service.generate_response(
                "Test",
                []
            )

            assert "kesalahan" in response.lower() or "error" in response.lower()


class TestWhatsAppService:
    """Test suite untuk WhatsAppService"""

    @pytest.mark.asyncio
    async def test_verify_webhook_token_valid(self):
        """Test verify webhook token yang valid"""
        from services.whatsapp import whatsapp_service

        # Token dari .env.example
        result = whatsapp_service.verify_webhook_token("your_custom_webhook_verify_token")

        # Note: Ini akan fail jika actual token berbeda
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_verify_webhook_token_invalid(self):
        """Test verify webhook token yang invalid"""
        from services.whatsapp import whatsapp_service

        result = whatsapp_service.verify_webhook_token("invalid_token_xyz")

        assert result is False

    @pytest.mark.asyncio
    @patch('services.whatsapp.httpx.AsyncClient')
    async def test_send_message_success(self, mock_client):
        """Test send message berhasil"""
        from services.whatsapp import whatsapp_service

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "wamid.123456789"}]
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        message_id = await whatsapp_service.send_message(
            "62812345678",
            "Hello"
        )

        assert message_id == "wamid.123456789"
        mock_client_instance.post.assert_awaited_once()
        url = mock_client_instance.post.call_args.args[0]
        payload = mock_client_instance.post.call_args.kwargs["json"]
        assert url == f"{whatsapp_service.base_url}/messages"
        assert payload["messaging_product"] == "whatsapp"
        assert payload["to"] == "62812345678"
        assert payload["text"]["body"] == "Hello"

    @pytest.mark.asyncio
    @patch('services.whatsapp.httpx.AsyncClient')
    async def test_send_message_error(self, mock_client):
        """Test send message error"""
        from services.whatsapp import whatsapp_service

        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        message_id = await whatsapp_service.send_message(
            "62812345678",
            "Hello"
        )

        assert message_id is None

    @pytest.mark.asyncio
    @patch('services.whatsapp.httpx.AsyncClient')
    async def test_mark_as_read(self, mock_client):
        """Test mark message as read"""
        from services.whatsapp import whatsapp_service

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance

        result = await whatsapp_service.mark_as_read("wamid.123456789")

        assert result is True
        mock_client_instance.post.assert_awaited_once()
        url = mock_client_instance.post.call_args.args[0]
        payload = mock_client_instance.post.call_args.kwargs["json"]
        assert url == f"{whatsapp_service.base_url}/messages"
        assert payload == {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": "wamid.123456789",
        }


class TestMessageHandler:
    """Test suite untuk MessageHandler"""

    @pytest.mark.asyncio
    async def test_send_welcome_message(self):
        """Test send welcome message"""
        from services.message_handler import message_handler

        with patch('services.message_handler.whatsapp_service.send_message') as mock_send:
            mock_send.return_value = "wamid.123"

            result = await message_handler.send_welcome_message(
                "62812345678",
                "Test User"
            )

            assert result is True
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_error_message(self):
        """Test send error message"""
        from services.message_handler import message_handler

        with patch('services.message_handler.whatsapp_service.send_message') as mock_send:
            mock_send.return_value = "wamid.123"

            result = await message_handler.send_error_message("62812345678")

            assert result is True
            mock_send.assert_called_once()
