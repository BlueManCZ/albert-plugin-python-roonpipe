"""
RoonPipe Albert Plugin - Search and play Roon tracks via RoonPipe socket
"""

import json
import socket
import time
from pathlib import Path

from albert import *

md_iid = '4.0'
md_version = '1.0'
md_name = 'RoonPipe'
md_description = 'Search and play Roon tracks via RoonPipe'
md_authors = ['BlueManCZ']


SOCKET_PATH = '/tmp/roonpipe.sock'
PLUGIN_DIR = Path(__file__).parent
ICON_PATH = Path(PLUGIN_DIR / 'icons' / 'roon.png')
DEBOUNCE_MS = 200  # Debounce delay in milliseconds


def make_roon_icon():
    """Create the Roon icon from a local file."""
    return makeImageIcon(str(ICON_PATH))


def send_command(command: dict) -> dict | None:
    """Send a command to RoonPipe socket and return the response."""
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect(SOCKET_PATH)
        sock.sendall(json.dumps(command).encode('utf-8'))

        response = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk

        sock.close()
        return json.loads(response.decode('utf-8'))
    except socket.timeout:
        return {'error': 'timeout'}
    except socket.error:
        return {'error': 'connection'}
    except json.JSONDecodeError:
        return {'error': 'parse'}


def search_tracks(query: str) -> tuple[list[dict], str | None]:
    """Search for tracks using RoonPipe.

    Returns:
        Tuple of (results list, error message / None)
    """
    response = send_command({'command': 'search', 'query': query})
    if response is None:
        return [], 'Connection failed'
    if response.get('error') == 'timeout':
        return [], 'Request timed out'
    if response.get('error') == 'connection':
        return [], 'Socket connection closed'
    if response.get('error') == 'parse':
        return [], 'Invalid response from RoonPipe'
    if response.get('error'):
        return [], str(response.get('error'))
    if response.get('results'):
        return response['results'], None
    return [], None


def play_track(item_key: str, session_key: str, action: str = 'play') -> bool:
    """Play a track using RoonPipe.

    Actions:
        - 'play': Replace queue and play immediately
        - 'playNow': Play immediately (preserves current queue)
        - 'addNext': Play next (add after current track)
        - 'queue': Add to the end of the queue
    """
    response = send_command({
        'command': 'play',
        'item_key': item_key,
        'session_key': session_key,
        'action': action
    })
    return response is not None and response.get('success', False)


class Plugin(PluginInstance, TriggerQueryHandler):

    def __init__(self):
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)

    def defaultTrigger(self) -> str:
        return 'roon '

    def synopsis(self, query: str) -> str:
        return 'Search for tracks...'

    def handleTriggerQuery(self, query: Query):
        query_string = query.string.strip()

        if not query_string:
            return

        # Debounce: wait before searching to avoid spamming on every keystroke
        time.sleep(DEBOUNCE_MS / 1000)
        if not query.isValid:
            return

        # Check if socket exists
        if not Path(SOCKET_PATH).exists():
            query.add(StandardItem(
                id='roonpipe-not-running',
                text='RoonPipe is not running',
                subtext='Start RoonPipe daemon first: roonpipe',
                icon_factory=make_roon_icon
            ))
            return

        # Search for tracks
        results, error = search_tracks(query_string)

        if error:
            query.add(StandardItem(
                id='roonpipe-error',
                text=error,
                subtext='Error occurred while searching Roon tracks',
                icon_factory=make_roon_icon
            ))
            return

        if not results:
            query.add(StandardItem(
                id='roonpipe-no-results',
                text='No tracks found',
                subtext=f'No results for "{query_string}"',
                icon_factory=make_roon_icon
            ))
            return

        items = []
        for i, result in enumerate(results):
            title = result.get('title', 'Unknown')
            subtitle = result.get('subtitle', '')
            item_key = result.get('item_key', '')
            session_key = result.get('sessionKey', '')
            image_path = result.get('image', '')

            # Use album art if available, otherwise fallback to Roon icon
            if image_path and Path(image_path).exists():
                icon_factory = lambda img=image_path: makeImageIcon(img)
            else:
                icon_factory = make_roon_icon

            items.append(StandardItem(
                id=f'roonpipe-track-{i}',
                text=title,
                subtext=subtitle,
                icon_factory=icon_factory,
                actions=[
                    Action(
                        id='playNow',
                        text='Play now',
                        callable=lambda ik=item_key, sk=session_key: play_track(ik, sk, 'playNow')
                    ),
                    Action(
                        id='addNext',
                        text='Play next',
                        callable=lambda ik=item_key, sk=session_key: play_track(ik, sk, 'addNext')
                    ),
                    Action(
                        id='queue',
                        text='Add to queue',
                        callable=lambda ik=item_key, sk=session_key: play_track(ik, sk, 'queue')
                    ),
                    Action(
                        id='playNow',
                        text='Play now and replace queue',
                        callable=lambda ik=item_key, sk=session_key: play_track(ik, sk, 'play')
                    ),
                ]
            ))

        query.add(items)
