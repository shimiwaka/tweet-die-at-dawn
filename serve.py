#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import http.server
import socketserver
import os
import sys
import socket
import urllib.parse
import signal
import atexit
import threading
import json
import time
import subprocess

SEND_TWEET_COMMAND = None
DELETE_TWEET_COMMAND = None

def load_commands():
    global SEND_TWEET_COMMAND, DELETE_TWEET_COMMAND
    
    try:
        with open('send_tweet_command.dat', 'r', encoding='utf-8') as f:
            SEND_TWEET_COMMAND = f.read().strip()
    except Exception as e:
        print(f"Error loading send_tweet_command.dat: {e}")
    
    try:
        with open('delete_tweet_command.dat', 'r', encoding='utf-8') as f:
            DELETE_TWEET_COMMAND = f.read().strip()
    except Exception as e:
        print(f"Error loading delete_tweet_command.dat: {e}")

def execute_command(command):
    try:
        output_file = 'command_output.tmp'
        error_file = 'command_error.tmp'
        
        cmd = f'{command} > {output_file} 2> {error_file}'
        exit_status = os.system(cmd)
        
        output = ''
        error = ''
        
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                output = f.read()
        except Exception:
            pass
        
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                error = f.read()
        except Exception:
            pass
        
        try:
            os.remove(output_file)
        except Exception:
            pass
        
        try:
            os.remove(error_file)
        except Exception:
            pass
        
        return {
            'output': output,
            'error': error,
            'status': exit_status
        }
    except Exception as e:
        return {
            'output': '',
            'error': str(e),
            'status': 1
        }

class TextFormHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/styles.css':
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            
            try:
                with open('styles.css', 'rb') as f:
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, "CSS file not found")
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>1時間後に消えるツイート</title>
            <link rel="stylesheet" href="/styles.css">
        </head>
        <body>
            <div class="form-container">
                <h2>1時間後に消えるツイート</h2>
                <form method="post" action="/submit">
                    <textarea name="text" placeholder="Enter your tweet here..."></textarea>
                    <button type="submit">つぶやく</button>
                </form>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        if self.path == '/submit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            content_type = self.headers.get('Content-Type', '')
            text = ''
            
            try:
                form_data = urllib.parse.parse_qs(post_data.decode('utf-8'))
                text = form_data.get('text', [''])[0]
            except Exception:
                self.send_error(400, "Invalid form data")
                return
            
            message = ""
            tweet_id = None
            
            global SEND_TWEET_COMMAND
            if SEND_TWEET_COMMAND is None:
                load_commands()
            
            if SEND_TWEET_COMMAND is None:
                message = "Error: Could not load tweet command"
            else:
                try:
                    command = SEND_TWEET_COMMAND.replace('TWEET_CONTENT', text)
                    
                    result = execute_command(command)
                    
                    if result['status'] == 0:
                        message = "Tweet sent successfully"
                        
                        try:
                            output = result['output']
                            response_data = json.loads(output)
                            if 'data' in response_data and 'create_tweet' in response_data['data']:
                                tweet_id = response_data['data']['create_tweet']['tweet_results']['result']['rest_id']
                                message += f" (ID: {tweet_id})"
                                
                                if tweet_id:
                                    threading.Thread(target=self.schedule_tweet_deletion, args=(tweet_id,)).start()
                        except Exception as e:
                            message += f" (Failed to get tweet ID: {str(e)})"
                    else:
                        error_msg = result['error'] or "Unknown error"
                        message = f"Failed to send tweet: {error_msg}"
                except Exception as e:
                    message = f"An error occurred: {str(e)}"
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>1時間後に消えるツイート</title>
                <link rel="stylesheet" href="/styles.css">
            </head>
            <body>
                <div class="form-container">
                    <h2>送信完了</h2>
                    <p>{}</p>
                    <p>このツイートは1時間後に自動的に削除されます。</p>
                    <p><a href="/">もどる</a></p>
                </div>
            </body>
            </html>
            """.format(message)
            
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404)
    
    def schedule_tweet_deletion(self, tweet_id):
        # 1時間待機
        time.sleep(3600)
        
        try:
            # delete_tweet.rbを実行
            command = f"ruby delete_tweet.rb {tweet_id}"
            result = execute_command(command)
            
            if result['status'] == 0:
                print(f"Tweet {tweet_id} deleted successfully")
            else:
                error_msg = result['error'] or "Unknown error"
                print(f"Failed to delete tweet {tweet_id}: {error_msg}")
        except Exception as e:
            print(f"Error deleting tweet {tweet_id}: {str(e)}")

class HTTPServer:
    def __init__(self, port=8000):
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
    
    def start(self):
        handler = TextFormHandler
        
        load_commands()
        
        try:
            self.server = socketserver.TCPServer(("", self.port), handler)
            self.server.allow_reuse_address = True
        except socket.error as e:
            if e.errno == 98 or e.errno == 10048:
                print(f"Error: Port {self.port} is already in use")
                print("Try a different port with: python serve.py [port]")
            else:
                print(f"Error creating server: {e}")
            return False
        
        print(f"Text form server started at http://localhost:{self.port}")
        print("Press Ctrl+C to stop the server")
        
        self.running = True
        self.server_thread = threading.Thread(target=self._serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        return True
    
    def _serve_forever(self):
        try:
            self.server.serve_forever()
        except Exception as e:
            if self.running:
                print(f"Error running server: {e}")
    
    def stop(self):
        if self.server and self.running:
            print("Shutting down server and releasing port...")
            self.running = False
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            print("Server stopped and port released")

def signal_handler(sig, frame):
    print("\nReceived termination signal. Shutting down...")
    if server:
        server.stop()
    sys.exit(0)

if __name__ == "__main__":
    port = 8000
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port < 1 or port > 65535:
                print(f"Error: Port must be between 1 and 65535")
                sys.exit(1)
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            print("Usage: python serve.py [port]")
            sys.exit(1)
    
    server = HTTPServer(port)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    atexit.register(lambda: server.stop() if server else None)
    
    success = server.start()
    if not success:
        sys.exit(1)
    
    try:
        while server.running:
            signal.pause()
    except KeyboardInterrupt:
        pass 