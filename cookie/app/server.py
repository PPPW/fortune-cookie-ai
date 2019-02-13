from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn, aiohttp, asyncio
from io import BytesIO
import random

from fastai import *
from fastai.vision import *

export_file_url = 'https://www.dropbox.com/s/vay47aricy4tdou/cookie_export.pkl?dl=1'
export_file_name = 'cookie_export.pkl'

starter = ['you', 'the', 'a', 'your', 'if', 'it', 'do', 'be', "don't", 'never', 'there', 'love', 'when', "it's", 'life', 'all', 'to', 'an', 'in', 'keep', 'everything', 'we', 'i', 'today', 'people', 'nothing', 'let', 'stop', 'for', 'good']
path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory=path/'static'))

async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f: f.write(data)

async def setup_learner():
    await download_file(export_file_url, path/'models'/export_file_name)
    try:
        learn = load_learner(path/'models', export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise

def format_output(sentence):    
    try:
        last_period = sentence.rindex('.')
        sentence = sentence[:last_period+1]
    except ValueError:
        sentence += ' .'
    words = sentence.split()
    res = words[0].capitalize()
    for i in range(1, len(words)):
        if words[i] in ['xxmaj', 'xxup']: continue   
        if words[i] == 'xxbos': break
        if words[i] in '.,!?:;"' or words[i][0] == '\'' or words[i][:2] == 'n\'':            
            res += words[i]
            continue
        res += ' '
        if words[i-1] == 'xxmaj': 
            res += words[i].capitalize()
        elif words[i-1] == 'xxup':
            res += words[i].upper()
        else:
            res += words[i]
    return res


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()

@app.route('/')
def index(request):
    html = path/'view'/'index.html'
    return HTMLResponse(html.open().read())

@app.route('/gen_sentence', methods=['POST'])
async def gen_sentence(request):    
    prediction = learn.predict(random.choice(starter) + ' ', 30, temperature=0.75)
    return JSONResponse({'result': format_output(prediction)})

if __name__ == '__main__':
    if 'serve' in sys.argv: uvicorn.run(app=app, host='0.0.0.0', port=5042)
