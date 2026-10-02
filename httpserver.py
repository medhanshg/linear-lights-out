
import socket
import traceback
from datetime import date
from urllib.parse import unquote_plus
# https://docs.python.org/3/library/random.html
import random   

current_player = ""
move_count = 0
best_scores = {}    
game_on = False

def get_requested_method(request_line): 
    return request_line.split(" ")[0]

def parse_post_request_form_fields(headers, reader_from_browser): 
    content_length = int(headers["Content-Length"])
    post_body = reader_from_browser.read(content_length)
    print("RAW Body:", post_body)
    post_body = post_body.decode("utf-8")
    form_fields={}

    if "&" in post_body:
        post_lines = post_body.split("&")
        for item in post_lines: 
            if not item:
                continue
            pair = item.split("=")
            key = unquote_plus(pair[0]).strip()
            value = unquote_plus(pair[1]).strip() 
            form_fields[key] = value

    else: 
        post_lines = post_body.replace("\r\n", "\n").split("\n")
        for line in post_lines: 
            if not line.strip():
                continue
            pair = line.split("=")
            key = unquote_plus(pair[0]).strip()
            value = unquote_plus(pair[1]).strip() if len(pair) > 1 else ""
            form_fields[key] = value

    return form_fields
     
def parse_headers(reader_from_browser): 
    headers={}
    header_line = reader_from_browser.readline().decode("utf-8")
    while (True):
        if header_line == "\r\n": 
            break
        pair = header_line.split(": ")
        headers[pair[0]] = pair[1].strip() 
        header_line = reader_from_browser.readline().decode("utf-8") 
    return headers

def get_requested_filename(request_line):
    parts = request_line.split()
    path = parts[1]
    if path == "/":
        path = "/startgame.html"
    return "." + path

def get_file_type(file_name):
    return "." + file_name.split(".")[-1]

def get_content_type(file_extension):
    if file_extension == ".html" or file_extension == ".htm":
        return "text/html; charset=utf-8"
    elif file_extension == ".txt":
        return "text/plain; charset=utf-8"
    elif file_extension == ".jpg" or file_extension == ".jpeg":
        return "image/jpeg"
    elif file_extension == ".png":
        return "image/png"
    elif file_extension == ".css":
        return "text/css; charset=utf-8"
    elif file_extension == ".ico":
        return "image/x-icon"
    elif file_extension == ".js":
        return "text/javascript; charset=utf-8"
    else:
        return "application/octet-stream"

# This function (and the following) was moved here for clarity,
# but is the same thing we have done in the
# past to handle special routes like /shutdown and getting request bodies
def handle_special_routes(requested_filename, connection_to_browser):
    if requested_filename == "./shutdown":
        print("Server shutting down")
        shutdown_connection(connection_to_browser)
        exit()

def get_file_body_in_bytes(requested_filename):
    with open(requested_filename, "rb") as fd:
        return fd.read()

def main(testing_flags=None):
    # Do not change the following code. This is here to allow us to manage part of your server
    # during testing.
    flags = initialize_flags(testing_flags)
    server = create_connection(port = 8080)
    global lights, current_player, move_count, best_scores, game_on

    while flags["continue"]:
        # Wait for the browser to send a HTTP Request
        connection_to_browser = accept_browser_connection_to(server)

        # Read the HTTP Request from the browser
        reader_from_browser = connection_to_browser.makefile(mode='rb')
        try:
            request_line = reader_from_browser.readline().decode("utf-8") # decode converts from bytes to text
            print()
            print('Request:')
            print(request_line)
        except Exception as e:
            print("Error while reading HTTP Request:", e)
            traceback.print_exc() # Print what line the server crashed on.
            shutdown_connection(connection_to_browser)
            continue

        # Gets the requested filename, extension, and file type
        requested_filename = get_requested_filename(request_line)
        file_extension = get_file_type(requested_filename)
        content_type = get_content_type(file_extension)

        # DONE: Get the requested HTTP Method
        # Implement a new get_requested_method function, which takes the
        # request line, and then call it here
        requested_method = get_requested_method(request_line); 

        # DONE: Print requested method
        print("Requested file:", requested_filename)
        print("Extension:", file_extension)
        print("Requested method: ",requested_method)

        # DONE: Read all Headers into a Dictionary
        # Implement a new parse_headers function, which takes the
        # browser stream (called reader_from_browser),
        # and then call it here
        headers = parse_headers(reader_from_browser)
        print("Headers: ",headers)

        # Move handling shutdown to a new function for clarity
        handle_special_routes(requested_filename, connection_to_browser)

        # Write the HTTP Response back to the browser
        writer_to_browser = connection_to_browser.makefile(mode='wb')
        try:
            # DONE: Handle GET and POST requests differently
            # The code below is what we did before to handle GET requests,
            # but it's been partially moved into a function for clarity.
            if requested_method == "GET":
                if requested_filename == "./game.html":
                    if game_on:
                        btns = ""
                        for i in range(len(lights)):
                            symbol = lights[i]
                            if symbol == "O":
                                btn_class = "on"
                            else:
                                btn_class = "off"
                            btns += '<form action="/toggle_light" method="POST">'
                            btns += '<button type="submit" name="button_index" value="' + str(i+1) + '" class="' + btn_class + '">' + symbol + '</button>'
                            btns += '</form>'
                        with open("./game.html", "rb") as fd:
                            html_contents = fd.read().decode("utf-8")
                        response_body = html_contents.format(game_load=btns).encode('utf-8')
                    else:
                        response_body = b"403 Forbidden"
                        content_type = "text/plain; charset=utf-8"

                elif requested_filename == "./bestscores.html":
                        table_rows = ""
                        for m in best_scores:
                            data = best_scores[m]
                            table_rows += "<tr>"
                            table_rows += "<td>" + str(m) + "</td>"
                            table_rows += "<td>" + str(data['moves']) + "</td>"
                            table_rows += "<td>" + str(data['player']) + "</td>"
                            table_rows += "<td>" + str(data['date']) + "</td>"
                            table_rows += "</tr>"
                        with open("./bestscores.html", "rb") as fd:
                             html_contents = fd.read().decode("utf-8")
                        response_body = html_contents.format(score_rows=table_rows).encode("utf-8")
                
                else:
                    try:
                        response_body = get_file_body_in_bytes(requested_filename)
                    except FileNotFoundError:
                        response_body = b"404 Not Found"
                        content_type = "text/plain; charset=utf-8"

            elif requested_method == "POST": 
                form_fields = parse_post_request_form_fields(headers, reader_from_browser)
                print("Received POST form fields:", form_fields)

                if requested_filename == "./game.html":
                    print("Starting a new game with parameters:", form_fields)
                    game_on = True
                    number_of_lights = int(form_fields.get("number_of_lights",5))
                    off_count = int(form_fields.get("off_lights") or 0)
                    current_player = form_fields.get("player_name")
                    move_count=0
                    lights = ["O"] * number_of_lights
                    if off_count>0:
                         randomi = random.sample(range(number_of_lights),off_count)
                         for j in randomi: 
                            lights[j]="X"
                    btns = ""   
                    for i in range(number_of_lights):
                       symbol = lights[i]
                       if symbol == "O":
                            btn_class = "on"
                       else:
                            btn_class = "off"
                       btns += '<form action="/toggle_light" method="POST">'
                       btns += '<button type="submit" name="button_index" value="' + str(i+1) + '" class="' + btn_class + '">' + symbol + '</button>'
                       btns += '</form>'
                    with open("./game.html", "rb") as fd:
                        html_contents = fd.read().decode("utf-8")
                    response_body = html_contents.format(game_load=btns)
                    response_body = response_body.encode('utf-8')

                    
                elif requested_filename == "./toggle_light":
                    content_type = "text/html; charset=utf-8"
                    move_count = move_count+1; 
                    clickedi = (int(form_fields.get("button_index", 1)))-1
                    switchi = [clickedi, clickedi-1, clickedi+1]
                    for k in switchi: 
                        if 0 <= k <len(lights):
                            if lights[k] == "O":
                                lights[k] = "X"
                            else:
                                lights[k] = "O"
                    game_won = True 
                    for l in lights: 
                         if l == "O":
                            game_won = False
                            break
                    if game_won:
                        game_on = False
                        today_str = str(date.today())
                        if len(lights) not in best_scores or move_count < best_scores[len(lights)]["moves"]:
                            best_scores[len(lights)] = {
                                "moves": move_count,
                                "player": current_player,
                                "date": today_str
                            }
                        table_rows = ""
                        for n in best_scores:
                            data = best_scores[n]
                            table_rows += "<tr>"
                            table_rows += "<td>" + str(n) + "</td>"
                            table_rows += "<td>" + str(data['moves']) + "</td>"
                            table_rows += "<td>" + str(data['player']) + "</td>"
                            table_rows += "<td>" + str(data['date']) + "</td>"
                            table_rows += "</tr>" 
                        with open("./bestscores.html", "rb") as fd:
                            html_contents = fd.read().decode("utf-8")
                        response_body = html_contents.format(score_rows=table_rows).encode('utf-8')
                    else:
                            btns = ""
                            for i in range(len(lights)):
                                symbol = lights[i]
                                if symbol == "O":
                                    btn_class = "on"
                                else:
                                    btn_class = "off"
                                btns += '<form action="/toggle_light" method="POST">'
                                btns += '<button type="submit" name="button_index" value="' + str(i+1) + '" class="' + btn_class + '">' + symbol + '</button>'
                                btns += '</form>'
                            
                            with open("./game.html", "rb") as fd:
                                html_contents = fd.read().decode("utf-8")

                            response_body = html_contents.format(game_load=btns)
                            response_body = response_body.encode('utf-8')

                elif requested_filename == "./bestscores.html":
                    table_rows = ""
                    for m in best_scores: 
                        data = best_scores[m]
                        table_rows += "<tr>"
                        table_rows += "<td>" + str(m) + "</td>"
                        table_rows += "<td>" + str(data['moves']) + "</td>"
                        table_rows += "<td>" + str(data['player']) + "</td>"
                        table_rows += "<td>" + str(data['date']) + "</td>"
                        table_rows += "</tr>"
                        
                    with open("./bestscores.html", "rb") as fd:
                        html_contents = fd.read().decode("utf-8")
                    response_body = html_contents.format(score_rows=table_rows).encode('utf-8')
                    
            else:
                try:
                    response_body = get_file_body_in_bytes(requested_filename)
                except FileNotFoundError:
                    response_body = b"404 Not Found"
               

            response_headers = "\r\n".join([
                'HTTP/1.1 200 OK',
                f'Content-Type: {content_type}',
                f'Content-length: {len(response_body)}',
                'Connection: close',
                '\r\n'
            ]).encode("utf-8")

            # These lines just PRINT the HTTP Response to your Terminal.
            print()
            print('Response headers:')
            print(response_headers)
            print()
            print('Response body:')
            print(response_body)
            print()

            # These lines do the real work; they write the HTTP Response to the Browser.
            writer_to_browser.write(response_headers)
            writer_to_browser.write(response_body)
            writer_to_browser.flush()
        except Exception as e:
            print("Error while writing HTTP Response:", e)
            flags["exceptions"].append(e)
            traceback.print_exc() # print what line the server crashed on
    
        shutdown_connection(connection_to_browser)



# Don't worry about the details of the rest of the code below.
# It is VERY low-level code for creating the underlying connection to the browser.

def create_connection(port):
    addr = ("", port)  # "" = all network adapters; usually what you want.
    server = socket.create_server(addr, family=socket.AF_INET6, dualstack_ipv6=True) # prevent rare IPV6 softlock on localhost connections
    server.settimeout(2)
    print(f'Server started on port {port}. Try: http://localhost:{port}/startgame.html')
    return server

def accept_browser_connection_to(server):
    while True:
        try:
            (conn, address) = server.accept()
            conn.settimeout(2)
            return conn
        except socket.timeout:
            print(".", end="", flush=True)
        except KeyboardInterrupt:
            exit(0)

def shutdown_connection(connection_to_browser):
    connection_to_browser.shutdown(socket.SHUT_RDWR)
    connection_to_browser.close()

def initialize_flags(testing_flags):
    flags = testing_flags if testing_flags is not None else {}
    if "continue" not in flags:
        flags["continue"] = True
    if "exceptions" not in flags:
        flags["exceptions"] = []
    return flags

if __name__ == "__main__":
    main()