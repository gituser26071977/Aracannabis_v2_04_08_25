import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self, calendar_id: str = None):
        self.calendar_id = calendar_id or os.getenv("GOOGLE_CALENDAR_ID")
        self.credentials_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "/app/config/service_account.json")
        self.service = None
        self._authenticate()

    def _authenticate(self):
        try:
            if not os.path.exists(self.credentials_path):
                print(f"DEBUG: [Google Calendar Service] Arquivo de credenciais não encontrado em {self.credentials_path}. Operando em modo Mock.", flush=True)
                logger.warning(f"Arquivo de credenciais não encontrado em {self.credentials_path}. Operando em modo Mock.")
                return

            scopes = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/calendar.events']
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path, scopes=scopes
            )
            self.service = build('calendar', 'v3', credentials=creds)
            print("DEBUG: [Google Calendar Service] Autenticado com sucesso via JSON.", flush=True)
            logger.info("Google Calendar Service autenticado com sucesso.")
        except Exception as e:
            print(f"DEBUG: [Google Calendar Service] Erro crítico na autenticação: {e}", flush=True)
            logger.error(f"Erro ao autenticar no Google Calendar: {e}")

    def get_upcoming_events(self, max_results=10):
        if not self.service:
            return []
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId=self.calendar_id, timeMin=now,
                maxResults=max_results, singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            logger.error(f"Erro ao buscar eventos: {e}")
            return []

    def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        """
        Verifica se um horário está livre.
        """
        if not self.service:
            # Mock: sempre diz que está ocupado se não configurado (seguro) ou livre (depende da política)
            return True 
        
        try:
            body = {
                "timeMin": start_time.isoformat() + 'Z',
                "timeMax": end_time.isoformat() + 'Z',
                "items": [{"id": self.calendar_id}]
            }
            
            freebusy_result = self.service.freebusy().query(body=body).execute()
            busy_slots = freebusy_result.get('calendars', {}).get(self.calendar_id, {}).get('busy', [])
            
            return len(busy_slots) == 0
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade: {e}")
            return False

    def list_free_slots(self, date: datetime, start_hour=9, end_hour=18) -> list:
        """
        Lista horários livres simplificados para um dia.
        """
        if not self.service:
            return ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"] # Mock

        # Regra Dr. Anderson: Não atende Segundas (0), Sábados (5) ou Domingos (6)
        if date.weekday() in [0, 5, 6]:
            return []

        free_slots = []
        # Garantir que não pegamos horários retroativos se for hoje
        now = datetime.now()
        actual_start = start_hour
        if date.date() == now.date():
            actual_start = max(start_hour, now.hour + 1)

        for hour in range(actual_start, end_hour):
            slot_start = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            slot_end = slot_start + timedelta(hours=1)
            
            if self.check_availability(slot_start, slot_end):
                free_slots.append(slot_start.strftime("%H:%M"))
        
        return free_slots

        return free_slots

    def create_event(self, start_time: datetime, end_time: datetime, summary: str, description: str = "", attendee_email: str = None):
        """
        Cria um evento real no Google Calendar.
        """
        if not self.service:
            print(f"DEBUG: [Google Calendar Service] MOCK: Criando evento '{summary}'", flush=True)
            return {"id": "mock_event_id"}

        try:
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
            }
            if attendee_email:
                event['attendees'] = [{'email': attendee_email}]
                event['sendUpdates'] = 'all'

            event_result = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            print(f"DEBUG: [Google Calendar Service] Evento criado: {event_result.get('htmlLink')}", flush=True)
            return event_result
        except Exception as e:
            logger.error(f"Erro ao criar evento: {e}")
            print(f"DEBUG: [Google Calendar Service] Erro ao criar evento: {e}", flush=True)
            return None

    def update_event(self, event_id: str, start_time: datetime, end_time: datetime, summary: str, description: str = "", attendee_email: str = None):
        """
        Atualiza um evento existente no Google Calendar.
        """
        if not self.service:
            print(f"DEBUG: [Google Calendar Service] MOCK: Atualizando evento '{event_id}'", flush=True)
            return {"id": event_id}

        try:
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
            }
            if attendee_email:
                event['attendees'] = [{'email': attendee_email}]

            updated_event = self.service.events().update(calendarId=self.calendar_id, eventId=event_id, body=event).execute()
            print(f"DEBUG: [Google Calendar Service] Evento atualizado: {updated_event.get('htmlLink')}", flush=True)
            return updated_event
        except Exception as e:
            logger.error(f"Erro ao atualizar evento {event_id}: {e}")
            return None

    def delete_event(self, event_id: str):
        """
        Exclui um evento do Google Calendar.
        """
        if not self.service:
            print(f"DEBUG: [Google Calendar Service] MOCK: Excluindo evento '{event_id}'", flush=True)
            return True

        try:
            self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
            print(f"DEBUG: [Google Calendar Service] Evento excluído: {event_id}", flush=True)
            return True
        except Exception as e:
            logger.error(f"Erro ao excluir evento {event_id}: {e}")
            return False

    def get_events_by_range(self, start_time: datetime, end_time: datetime):
        """
        Busca eventos em um intervalo específico.
        """
        if not self.service:
            return []

        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            logger.error(f"Erro ao buscar eventos por intervalo: {e}")
            return []

# Instância padrão (será configurada via ENV)
calendar_service = GoogleCalendarService()
