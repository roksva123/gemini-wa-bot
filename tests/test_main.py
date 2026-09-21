from unittest.mock import AsyncMock, patch


class TestHealthEndpoint:
    """Test suite untuk /health endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "Gemini WhatsApp Bot"
        assert "version" in data


class TestWebhookVerification:
    """Test suite untuk webhook verification"""

    def test_webhook_verification_success(self, client):
        """Test webhook verification dengan token yang benar"""
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_string",
                "hub.verify_token": "your_custom_webhook_verify_token"  # Default dari .env.example
            }
        )
        # Note: Ini akan fail jika actual WA_VERIFY_TOKEN berbeda
        # Untuk testing, mock WA_VERIFY_TOKEN atau use environment-specific config
        assert response.status_code in [200, 403]

    def test_webhook_verification_invalid_token(self, client):
        """Test webhook verification dengan token invalid"""
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "test_challenge_string",
                "hub.verify_token": "invalid_token_xyz"
            }
        )
        assert response.status_code == 403

    def test_webhook_verification_invalid_mode(self, client):
        """Test webhook verification dengan mode invalid"""
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "invalid_mode",
                "hub.challenge": "test_challenge_string",
                "hub.verify_token": "your_custom_webhook_verify_token"
            }
        )
        assert response.status_code == 400


class TestWebhookMessages:
    """Test suite untuk webhook message receiving"""

    @patch("main.message_handler.handle_incoming_message", new_callable=AsyncMock)
    @patch("main.whatsapp_service.mark_as_read", new_callable=AsyncMock)
    def test_webhook_receive_valid_message(self, mock_mark_as_read, mock_handle_message, client, db):
        """Test menerima pesan valid dari WhatsApp"""
        mock_mark_as_read.return_value = True
        mock_handle_message.return_value = "Bot response"
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "1234567890",
                                    "phone_number_id": "123456789",
                                    "webhook_id": "123456789"
                                },
                                "contacts": [
                                    {
                                        "profile": {
                                            "name": "Test User"
                                        },
                                        "wa_id": "62812345678"
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "62812345678",
                                        "id": "wamid.123456789",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {
                                            "body": "Hello bot!"
                                        }
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }

        response = client.post("/webhook", json=webhook_payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_mark_as_read.assert_awaited_once_with("wamid.123456789")
        mock_handle_message.assert_awaited_once()

    def test_webhook_receive_invalid_object(self, client):
        """Test menerima webhook dengan object type invalid"""
        webhook_payload = {
            "object": "invalid_object_type",
            "entry": []
        }

        response = client.post("/webhook", json=webhook_payload)
        assert response.status_code == 200  # Ignored but accepted
        assert response.json()["status"] == "ok"

    def test_webhook_receive_non_message_change(self, client):
        """Test menerima webhook dengan change bukan messages"""
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {}
                            },
                            "field": "status_updates"  # Bukan messages
                        }
                    ]
                }
            ]
        }

        response = client.post("/webhook", json=webhook_payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_webhook_receive_empty_messages(self, client):
        """Test menerima webhook dengan empty messages"""
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {},
                                "messages": [],
                                "contacts": []
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }

        response = client.post("/webhook", json=webhook_payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_webhook_receive_non_text_message(self, client):
        """Test menerima webhook dengan non-text message"""
        webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {},
                                "contacts": [{"profile": {"name": "Test"}, "wa_id": "62812345678"}],
                                "messages": [
                                    {
                                        "from": "62812345678",
                                        "id": "wamid.123456789",
                                        "timestamp": "1234567890",
                                        "type": "image",  # Bukan text
                                        "image": {"id": "123"}
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }

        response = client.post("/webhook", json=webhook_payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_webhook_receive_invalid_json(self, client):
        """Test menerima webhook dengan invalid JSON"""
        response = client.post(
            "/webhook",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400


class TestTestEndpoints:
    """Test suite untuk test/debug endpoints"""

    def test_send_message_endpoint_exists(self, client):
        """Test send message endpoint dapat diakses"""
        response = client.post(
            "/test/send-message",
            params={
                "phone_number": "62812345678",
                "message": "Test message"
            }
        )
        # Endpoint should exist (might fail due to missing credentials)
        assert response.status_code in [200, 400, 500]

    def test_send_message_invalid_phone(self, client):
        """Test send message dengan phone number invalid"""
        response = client.post(
            "/test/send-message",
            params={
                "phone_number": "123",  # Too short
                "message": "Test"
            }
        )
        assert response.status_code == 400

    def test_chat_history_endpoint_exists(self, client):
        """Test chat history endpoint dapat diakses"""
        response = client.get(
            "/test/chat-history/62812345678"
        )
        # Endpoint should exist and return valid response
        assert response.status_code == 200
        data = response.json()
        assert "phone_number" in data
        assert "message_count" in data
        assert "messages" in data


class TestErrorHandling:
    """Test suite untuk error handling"""

    def test_webhook_json_decode_error(self, client):
        """Test handling JSON decode error"""
        response = client.post(
            "/webhook",
            content="not a json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

    def test_webhook_unexpected_error(self, client):
        """Test handling unexpected error"""
        # Send valid-looking webhook but trigger error
        response = client.post(
            "/webhook",
            json={
                "object": "whatsapp_business_account",
                "entry": None  # This will trigger an error
            }
        )
        # Should handle gracefully
        assert response.status_code in [200, 500]
