import requests,random,os,json, re
from kokkoro import R,priv, aiorequests
from kokkoro.service import Service
from kokkoro.config import RES_DIR
from kokkoro.common_interface import EventInterface, KokkoroBot
from kokkoro.util import DailyNumberLimiter
import kokkoro

from PIL import Image

sv_help = '''
[今天吃什么] 看看今天吃啥
'''.strip()

sv = Service(
    name = '今天吃什么',  #功能名
    use_priv = priv.NORMAL, #使用权限
    manage_priv = priv.ADMIN, #管理权限
    visible = True, #可见性
    enable_on_default = True, #默认启用
    help_ = sv_help #帮助说明
    )

_day_limit = 5
_lmt = DailyNumberLimiter(_day_limit)
_dir = os.path.join(os.path.expanduser(kokkoro.config.RES_DIR), 'img', 'foods')

def get_foods():
    if os.path.exists(os.path.join(_dir, 'foods.json')):
        with open(os.path.join(_dir, 'foods.json'),"r",encoding='utf-8') as dump_f:
            try:
                words = json.load(dump_f)
            except Exception as e:
                kokkoro.logger.error(f'读取食谱时发生错误{type(e)}')
                return None
    else:
        kokkoro.logger.error(f'目录下未找到食谱')
    keys = list(words.keys())
    key = random.choice(keys)
    return words[key]

@sv.on_rex(r'^(今天|[早中午晚][上饭餐午]|夜宵)吃(什么|啥|点啥)')
async def net_ease_cloud_word(bot: KokkoroBot, ev: EventInterface):
    uid = ev.get_author_id()
    if not _lmt.check(uid):
        return
    """
    match = ev['match']
    time = match.group(1).strip()
    """
    food = get_foods()
    to_eat = f'去吃{food["name"]}吧~'
    try:
        if "pic" in food:
            foodimg = Image.open(os.path.join(_dir,f'{food["pic"]}.jpg'))
        else:
            foodimg = Image.open(os.path.join(_dir,f'{food["name"]}.jpg'))
        #to_eat = to_eat+foodimg
        #seperate the sending evts.
    except Exception as e:
        kokkoro.logger.error(f'读取食物图片时发生错误{type(e)}')
    await bot.kkr_send(ev, to_eat, at_sender=True)
    await bot.kkr_send(ev, foodimg, at_sender=True)
    _lmt.increase(uid)

async def download_async(url: str, save_path: str, save_name: str, auto_extension=False):
    resp= await aiorequests.get(url, stream=True)
    if resp.status_code == 404:
        raise ValueError('文件不存在')
    content = await resp.content
    if auto_extension: #没有指定后缀，自动识别后缀名
        try:
            extension = filetype.guess_mime(content).split('/')[1]
        except:
            raise ValueError('不是有效文件类型')
        abs_path = os.path.join(save_path, f'{save_name}.{extension}')
    else:
        abs_path = os.path.join(save_path, save_name)
    with open(abs_path, 'wb') as f:
        f.write(content)
        return abs_path

# Todo
@sv.on_prefix('添菜')
async def add_food(bot: KokkoroBot, ev: EventInterface):
    #if not priv.check_priv(ev, priv.ADMIN):
    if not priv.check_priv(ev.get_author(), priv.ADMIN):
        await bot.kkr_send(ev,'此命令仅管理员可用~')
        return
    #food = ev.message.extract_plain_text().strip()
    food = ev.get_content().strip()
    #ret = re.search(r"\[CQ:image,file=(.*)?,url=(.*)\]", str(ev.message))
    #ret = re.search(r"\[CQ:image,file=(.*)?,url=(.*)\]", ev.get_content())
    ret = re.search('.', ev.get_content())
    if not ret:
        await bot.kkr_send(ev,'请附带美食图片~')
        return
    #hash = ret.group(1)
    url = ev.get_content()
    savepath = os.path.join(os.path.expanduser(RES_DIR), 'img', 'foods')
    if not os.path.exists(savepath):
        os.mkdir(savepath)
    imgpath = await download_async(url, savepath, str(food), auto_extension=True)
    pic = os.path.split(imgpath)[1]
    with open(os.path.join(_dir, 'foods.json'),"r",encoding='utf-8') as dump_f:
        words = json.load(dump_f)
    words[hash] = {"name":food, "pic":pic}
    with open(os.path.join(_dir, 'foods.json'),'w',encoding='utf8') as f:
        json.dump(words, f, ensure_ascii=False,indent=2)
    await bot.kkr_send(ev,'食谱已增加~')


async def save_img(url): #从消息中拿图
    response = await aiorequests.get(url, headers=headers)
    image = Image.open(BytesIO(await response.content))
    info = image.info
