from django.test import TestCase
from unittest.mock import patch, MagicMock
from services.tasks import send_telegram_notification
import os

class TelegramNotificationTest(TestCase):

    @patch('requests.post')
    @patch('os.getenv')
    def test_send_to_multiple_admins(self, mock_getenv, mock_post):
        # 1. Muhit o'zgaruvchilarini soxtalashtiramiz
        def side_effect(key):
            values = {
                'TELEGRAM_BOT_TOKEN': 'test_token',
                'TELEGRAM_ADMIN_CHAT_ID': '12345,67890' # Ikkita ID
            }
            return values.get(key)
        
        mock_getenv.side_effect = side_effect

        # 2. Requests javobini soxtalashtiramiz
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        # 3. Funksiyani chaqiramiz
        results = send_telegram_notification(1, "Santexnika", "Kran buzuldi")

        # 4. TEKSHIRUVLAR (Assertions)
        # requests.post roppa-rosa 2 marta chaqirilgan bo'lishi kerak
        self.assertEqual(mock_post.call_count, 2)
        
        # Birinchi ID ga yuborilganini tekshirish
        first_call_args = mock_post.call_args_list[0]
        self.assertEqual(first_call_args[1]['data']['chat_id'], '12345')
        
        # Ikkinchi ID ga yuborilganini tekshirish
        second_call_args = mock_post.call_args_list[1]
        self.assertEqual(second_call_args[1]['data']['chat_id'], '67890')

        print("\nTDD Testi: Telegram bildirishnomasi bir nechta adminlarga to'g'ri yuborildi!")

    @patch('os.getenv')
    def test_missing_credentials(self, mock_getenv):
        # Ma'lumotlar bo'lmasa xato qaytarishini tekshirish
        mock_getenv.return_value = None
        result = send_telegram_notification(1, "Test", "Test")
        self.assertEqual(result, "Telegram credentials not found")
        print("TDD Testi: Ma'lumotlar yo'qligida xavfsizlik tekshiruvi ishladi!")
