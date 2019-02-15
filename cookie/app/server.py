from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn, aiohttp, asyncio
from io import BytesIO
import random

from fastai import *
from fastai.text import *

export_file_url = 'https://www.dropbox.com/s/vay47aricy4tdou/cookie_export.pkl?dl=1'
export_file_name = 'cookie_export.pkl'

starter = ['you', 'the', 'a', 'your', 'if', 'it', 'do', 'be', "don't", 'never', 'there', 'love', 'when', "it's", 'life', 'all', 'to', 'an', 'in', 'keep', 'everything', 'we', 'i', 'today', 'people', 'nothing', 'let', 'stop', 'for', 'good']
puncs = '.,!?:;"' + "'"
n_word = 3
device = None
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
        global device
        device = one_param(learn.model).device
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise

def predict(learn, text, n_words, reset, temperature=1., sep=' ', decoder=decode_spec_tokens):     
    new_idx = []
    if reset:
        xb,yb = learn.data.one_item(text)
        learn.model.reset()
        new_idx = [learn.data.vocab.stoi[TK_MAJ]] + xb.tolist()[0][1:]
    else:        
        if text[-1] in puncs: text = text[-1]
        xb = tensor([[learn.data.vocab.stoi[text]]]).to(device)
        yb = tensor([0]).to(device)
    i_BOS = learn.data.vocab.stoi[BOS]
    is_end = False    
    for _ in range(n_words):
        res = learn.pred_batch(batch=(xb,yb))[0][-1]
        res[learn.data.vocab.stoi[UNK]] = 0.        
        if temperature != 1.: res.pow_(1 / temperature)
        idx = torch.multinomial(res, 1).item()
        if idx == i_BOS: 
            is_end = True
            break
        new_idx.append(idx)
        xb = xb.new_tensor([idx])[None]    
    return sep.join(decoder(learn.data.vocab.textify(new_idx, sep=None))), is_end

def format_output(sentence):    
    for punc in puncs:
        sentence = sentence.replace(' ' + punc, punc)
    return sentence


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
    data = await request.form()
    word = data['word']
    reset = False
    if word == '':
        word = random.choice(starter)
        reset = True
    prediction, is_end = predict(learn, word, n_word, reset, temperature=0.75)
    #await asyncio.sleep(1)
    return JSONResponse({'result': format_output(prediction), 'end': is_end})

if __name__ == '__main__':
    if 'serve' in sys.argv: uvicorn.run(app=app, host='0.0.0.0', port=5042)
