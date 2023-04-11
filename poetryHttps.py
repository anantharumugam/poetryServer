#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import random
from bs4 import BeautifulSoup
import requests
import ssl
import json
import sys
import time

class Poetry:
    def __init__(self, cached_mode=0, cache_pages=150,rebuild_cache=0, magic = "99m99"):
        self.cached_mode = cached_mode
        self.cache_pages = cache_pages
        self.rebuild_cache = rebuild_cache
        self.poetry_cache = []
        self.magic = magic
        if self.rebuild_cache:
            print("Force rebuilding poetry cache")
            self.build_poetry_cache()
            self.save_poetry_cache()
        if self.cached_mode:
            self.load_poetry_cache()

    def get_magic(self):
        return self.magic

    def build_poetry_cache(self):
        page_num = 1 
        print("Building poetry cache \n")
        progress = "#" 
        while( page_num <= self.cache_pages ):
            poetry = self.get_poetry(page_num)
            print(progress)
            time.sleep(1)
            progress += "#" 
            self.poetry_cache += poetry
            page_num = page_num + 1 
            
    def save_poetry_cache(self):
        with open("poetry_cache.json", 'w') as f:
            json.dump(self.poetry_cache, f, indent=2)   

    def load_poetry_cache(self):
        try:
            with open("poetry_cache.json", 'r') as f:
                self.poetry_cache = json.load(f)
        except FileNotFoundError:
            self.build_poetry_cache()
            self.save_poetry_cache()
        except Exception as err:
            print("Exception occurred while opening json file ", err )
            print("Rebuilding the cache might help" )
            sys.exit(1)
        print("Total poetry in cache is ", len(self.poetry_cache))

    def get_css_string(self):
       style = "<style type=\"text/css\"> \n"
       style += "table.center { margin: 0 auto;font-size: 30px; }\n"
       style += "td:empty::after{ content: \"\\00a0\";} \n"
       style += "html, body { background-color:#303030; color:#F8F8F8; height:100%; width: 100%; }\n"
       style += "</style>\n"
       return style

    def get_html_output(self,poetry,author,book):
        output = "<html>\n<head>\n" + self.get_css_string() + "</head>\n"
        output += "<body> \n <table class=\"center\"> \n"
        output += "<tr><td></td></tr> \n"
        output += "<tr><td></td></tr> \n"
        output += "<tr><td></td></tr> \n"
        if book :
            output += "<tr><td></td></tr> \n"
            output += "<tr align='center' ><td> " + book + "</td></tr> \n"
        output += "<tr><td></td></tr> \n"
        output += "<tr><td>" + poetry +"</td></tr> \n"
        output += "<tr><td></td></tr> \n"
        output += "<tr align='right' ><td> By " + author +"</td></tr> \n"
        output += "</table> \n </body> \n </html> \n"
        return output

    def get_random_poetry(self):
        if self.cached_mode:
            p_index = random.randint(1,len(self.poetry_cache)-1)
            return self.poetry_cache[p_index]
        else:
            poetry = self.get_poetry(random.randint(1,150))
            p_index = random.randint(1,len(poetry)-1)
            return poetry[p_index]

    def get_poetry(self,page_num):
        quote_url='https://www.goodreads.com/quotes/tag/poetry'
        #page_num = page_num
        print("Picking page " , page_num )
        params = {'page':page_num}
        page = requests.get(quote_url,params)
        soup = BeautifulSoup(page.content, 'html.parser')
        quotes=[]
        for quote_text in soup.find_all('div', {'class': 'quoteText'}):
            try:
                try:
                    book = quote_text.find('a', {'class': 'authorOrTitle'}).text.encode('ascii','ignore').decode()
                except AttributeError:
                    book = None
                author_all_text = quote_text.find('span', {'class': 'authorOrTitle'}).text.encode('ascii','ignore').decode().replace(',', '').split('\n')
                author = author_all_text[1].strip()
                for br in quote_text('br'):
                    br.replace_with(self.magic)
                quote_all_text = quote_text.text.encode('ascii','ignore').decode().split('\n')
                quote = quote_all_text[1].strip()
                quotes.append({'author': author, 'book': book, 'poetry': quote})
            except:
                pass
        return quotes


class RequestHandler(BaseHTTPRequestHandler):
    poetryObj = None

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        poetry = self.poetryObj.get_random_poetry()
        poetry_str = poetry['poetry'].replace(self.poetryObj.get_magic(),"<br/>")
        html = self.poetryObj.get_html_output(poetry_str,poetry['author'],poetry['book'])
        self.wfile.write(html.encode())
        return

    def do_POST(self):
        content_len = int(self.headers.getheader('content-length'))
        self.send_response(200)
        self.end_headers()
        out_str = "Welcome to  Multiverse " + str(random.randint(100,1000))
        self.wfile.write((out_str).encode())
        return

class PoetryHttpsServer:
    def __init__(self,argList):
        self.prog_name = argList[0];
        self.args = argList[1:]
        self.parse_cache_args()
        self.parse_port()
        self.parse_key_cert()

    def usage(self):
        print("Usage:")
        print("\t sudo %s [--no-cache] [--cache-pages <num> ] [--force-rebuild] [--cert <certificate filename with path> --key <key filename with path>] --[port <portnum>]" % self.prog_name )
        sys.exit(1)

    def parse_cache_args(self):
        if "--no-cache" in self.args:
            self.cache_mode = 0
            if "--cache-pages" in self.args or "--force-rebuild" in self.args:
                print("--cache-pages and --force-rebuild are meaningless in --no-cache mode;Ignoring it.")
        else:
            self.cache_mode = 1
            self.parse_cache_pages()
            self.parse_force_rebuild()

    def get_arg_value(self,arg_name,default):
        if arg_name in self.args:
            index = self.args.index(arg_name)
            try:
                return self.args[index + 1]
            except:
                self.usage()
        else:
            return default
        
    def parse_cache_pages(self):
        self.cache_pages = int(self.get_arg_value("--cache-pages","150"))

    def parse_force_rebuild(self):
         self.force_rebuild = 1 if "--force-rebuild" in self.args else 0

    def parse_port(self):
        self.port = int(self.get_arg_value("--port","443"))

    def parse_key_cert(self):
        self.cert_file = self.get_arg_value("--cert","certificate.pem")
        self.key_file = self.get_arg_value("--key","private.pem")

    def print_args(self):
        print("using the below args:")
        print("self.cache_mode = " , self.cache_mode )
        print("self.cache_pages = " , self.cache_pages )
        print("self.force_rebuild = " , self.force_rebuild)
        print("self.port = " , self.port)
        print("self.cert_file = " , self.cert_file)
        print("self.key_file = " , self.key_file)

    def run(self):
        self.print_args()
        RequestHandler.poetryObj = Poetry(self.cache_mode,self.cache_pages,self.force_rebuild)
        httpd = HTTPServer(('0.0.0.0', self.port ), RequestHandler )
        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslctx.check_hostname = False 
        sslctx.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
        httpd.socket = sslctx.wrap_socket(httpd.socket, server_side=True)
        print("Starting HTTPS poetry server")
        httpd.serve_forever()


if __name__ == '__main__':
    poetryServer = PoetryHttpsServer(sys.argv)
    poetryServer.run()

