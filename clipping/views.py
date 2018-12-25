from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Clipping, User_Clipping, Book
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
import locale
import re, sys, codecs
import json
import os
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
import requests
from lxml import etree
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from aip import AipOcr

# 切换输出流编码为utf-8
if sys.stdout.encoding != 'UTF-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'UTF-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 分享图片生成类
class Img():

    def __init__(self, save_dir=None):
        self.save_dir = save_dir

        self.font_family = 'static/FZQingKeBenYueSong.TTF'
        self.font_size = 20  # 字体大小
        self.line_space = 20  # 行间隔大小
        self.word_space = 5
        self.share_img_width = 640
        self.padding = 50
        self.song_name_space = 50
        self.banner_space = 60
        self.text_color = '#767676'
        # self.netease_banner = unicode('来自网易云音乐•歌词分享', "utf-8")
        self.netease_banner = u'来自 Kindle·文摘分享'
        self.netease_banner_color = '#D3D7D9'
        self.netease_banner_size = 20
        self.netease_icon = 'static/img/kindle_icon.png'
        self.icon_width = 25

        self.style2_margin = 50
        self.style2_padding = 30
        self.style2_line_width = 2
        self.style2_quote_width = 30
        self.quote_icon = 'static/img/quote.png'

        if self.save_dir is not None:
            try:
                os.mkdir(self.save_dir)
            except:
                pass

    def save(self, name, lrc, img_url):
        lyric_font = ImageFont.truetype(self.font_family, self.font_size)
        banner_font = ImageFont.truetype(self.font_family, self.netease_banner_size)
        lyric_w, lyric_h = ImageDraw.Draw(Image.new(mode='RGB', size=(1, 1))).textsize(lrc, font=lyric_font,
                                                                                       spacing=self.line_space)

        padding = self.padding
        w = self.share_img_width

        album_img = None
        if img_url.startswith('http'):
            raw_img = requests.get(img_url)
            album_img = Image.open(BytesIO(raw_img.content))
        else:
            album_img = Image.open(img_url)

        iw, ih = album_img.size
        album_h = ih * w // iw

        h = album_h + padding + lyric_h + self.song_name_space + \
            self.font_size + self.banner_space + self.netease_banner_size + padding

        resized_album = album_img.resize((w, album_h), resample=3)
        icon = Image.open(self.netease_icon).resize((self.icon_width, self.icon_width), resample=3)

        out_img = Image.new(mode='RGB', size=(w, h), color=(255, 255, 255))
        draw = ImageDraw.Draw(out_img)

        # 添加封面
        out_img.paste(resized_album, (0, 0))

        # 添加文字
        draw.text((padding, album_h + padding), lrc, font=lyric_font, fill=self.text_color, spacing=self.line_space)

        # Python中字符串类型分为byte string 和 unicode string两种，'——'为中文标点byte string，需转换为unicode string
        y_song_name = album_h + padding + lyric_h + self.song_name_space
        # song_name = unicode('—— 「', "utf-8") + name + unicode('」', "utf-8")
        song_name = u'—— 「' + name + u'」'
        sw, sh = draw.textsize(song_name, font=lyric_font)
        draw.text((w - padding - sw, y_song_name), song_name, font=lyric_font, fill=self.text_color)

        # 添加网易标签
        y_netease_banner = h - padding - self.netease_banner_size
        out_img.paste(icon, (padding, y_netease_banner - 2))
        draw.text((padding + self.icon_width + 5, y_netease_banner), self.netease_banner, font=banner_font,
                  fill=self.netease_banner_color)

        img_save_path = ''
        if self.save_dir is not None:
            img_save_path = self.save_dir
        out_img.save(img_save_path + name + '.png')

    def save2(self, name, lrc, img_url, id):
        lyric_font = ImageFont.truetype(self.font_family, self.font_size)
        banner_font = ImageFont.truetype(self.font_family, self.netease_banner_size)
        lyric_w, lyric_h = ImageDraw.Draw(Image.new(mode='RGB', size=(1, 1))).\
            textsize(lrc, font=lyric_font, spacing=self.line_space)
        margin = self.style2_margin
        padding = self.style2_padding
        w = self.share_img_width
        h = margin + padding + lyric_h + self.song_name_space + \
            self.font_size + self.banner_space + self.netease_banner_size + padding + margin

        icon = Image.open(self.netease_icon).resize((self.icon_width, self.icon_width), resample=3)
        quote = Image.open(self.quote_icon).resize((self.style2_quote_width, self.style2_quote_width), resample=3)

        out_img = Image.new(mode='RGB', size=(w, h), color=(255, 255, 255))
        draw = ImageDraw.Draw(out_img)

        def draw_rectangle(draw, rect, width):
            for i in range(width):
                draw.rectangle((rect[0] + i, rect[1] + i, rect[2] - i, rect[3] - i), outline=self.netease_banner_color)

        # 画边框
        rect_h = padding + lyric_h + self.song_name_space + self.font_size + self.banner_space
        draw_rectangle(draw, (margin, margin, w - margin, margin + rect_h), 2)
        out_img.paste(quote, (margin - self.style2_quote_width // 2, margin + self.style2_quote_width // 2))
        quote = quote.rotate(180)
        out_img.paste(quote, (w - margin - self.style2_quote_width // 2,
                              margin + rect_h - self.style2_quote_width - self.style2_quote_width // 2))

        # 添加文字
        draw.text((margin + padding, margin + padding), lrc, font=lyric_font, fill=self.text_color,
                  spacing=self.line_space)

        y_song_name = margin + padding + lyric_h + self.song_name_space
        # song_name = unicode('—— 「', "utf-8") + name + unicode('」', "utf-8")
        song_name = u'—— 「' + name + u'」'
        sw, sh = draw.textsize(song_name, font=lyric_font)
        draw.text((w - margin - padding - sw, y_song_name), song_name, font=lyric_font, fill=self.text_color)

        # 添加网易标签
        y_netease_banner = h - padding - self.netease_banner_size
        out_img.paste(icon, (margin, y_netease_banner - 2))
        draw.text((margin + self.icon_width + 5, y_netease_banner), self.netease_banner, font=banner_font,
                  fill=self.netease_banner_color)

        img_save_path = ''
        if self.save_dir is not None:
            img_save_path = self.save_dir
        out_img.save(img_save_path + str(id) + '.png')

    def save3(self, name, lrc, img_url, id):
        lyric_font = ImageFont.truetype(self.font_family, self.font_size)
        banner_font = ImageFont.truetype(self.font_family, self.netease_banner_size)
        lyric_w, lyric_h = ImageDraw.Draw(Image.new(mode='RGB', size=(1, 1))).textsize(lrc, font=lyric_font,
                                                                                       spacing=self.line_space)

        margin = self.style2_margin
        padding = self.style2_padding
        w = self.share_img_width

        album_img = None
        # if img_url.startswith('http'):
        if len(img_url) == 2:
            raw_img = requests.get(img_url[0])
            if "AccessDenied" in str(raw_img.content):
                raw_img = requests.get(img_url[1])
            album_img = Image.open(BytesIO(raw_img.content))
        else:
            album_img = Image.open(img_url)

        iw, ih = album_img.size
        album_img = album_img.crop((0, 20, iw, ih/2+200))
        iw, ih = album_img.size
        album_h = ih * w // iw

        h = album_h + margin + padding + lyric_h + self.song_name_space + \
            self.font_size + self.banner_space + self.netease_banner_size + padding + margin

        resized_album = album_img.resize((w, album_h), resample=3)
        icon = Image.open(self.netease_icon).resize((self.icon_width, self.icon_width), resample=3)
        quote = Image.open(self.quote_icon).resize((self.style2_quote_width, self.style2_quote_width), resample=3)

        out_img = Image.new(mode='RGB', size=(w, h), color=(255, 255, 255))
        draw = ImageDraw.Draw(out_img)

        def draw_rectangle(draw, rect, width):
            for i in range(width):
                draw.rectangle((rect[0] + i, rect[1] + i, rect[2] - i, rect[3] - i), outline=self.netease_banner_color)

        # 添加封面
        out_img.paste(resized_album, (0, 0))

        # 画边框
        rect_h = padding + lyric_h + self.song_name_space + self.font_size + self.banner_space
        draw_rectangle(draw, (margin, album_h + margin, w - margin, album_h + margin + rect_h), 2)
        out_img.paste(quote, (margin - self.style2_quote_width // 2, album_h + margin + self.style2_quote_width // 2))
        quote = quote.rotate(180)
        out_img.paste(quote, (w - margin - self.style2_quote_width // 2,
                              album_h + margin + rect_h - self.style2_quote_width - self.style2_quote_width // 2))

        # 添加文字
        draw.text((margin + padding, album_h + margin + padding), lrc, font=lyric_font, fill=self.text_color,
                  spacing=self.line_space)

        y_song_name = album_h + margin + padding + lyric_h + self.song_name_space
        # song_name = unicode('—— 「', "utf-8") + name + unicode('」', "utf-8")
        song_name = u'—— 「' + name + u'」'
        sw, sh = draw.textsize(song_name, font=lyric_font)
        draw.text((w - margin - padding - sw, y_song_name), song_name, font=lyric_font, fill=self.text_color)

        # 添加网易标签
        y_netease_banner = h - padding - self.netease_banner_size
        out_img.paste(icon, (margin, y_netease_banner - 2))
        draw.text((margin + self.icon_width + 5, y_netease_banner), self.netease_banner, font=banner_font,
                  fill=self.netease_banner_color)

        img_save_path = ''
        if self.save_dir is not None:
            img_save_path = self.save_dir
        out_img.save(img_save_path + str(id) + '.png')

def index(request):
    return render(request, 'index.html')

def register(request):
    # 只有当请求为 POST 时，才表示用户提交了注册信息
    if request.method == 'POST':
        # request.POST 是一个类字典数据结构，记录了用户提交的注册信息
        # 这里提交的就是用户名（username）、密码（password）、邮箱（email）
        # 用这些数据实例化一个用户注册表单
        form = UserCreationForm(request.POST)

        # 验证数据的合法性
        if form.is_valid():
            # 如果提交数据合法，调用表单的 save 方法将用户数据保存到数据库
            form.save()

            # 注册成功，跳转回首页
            return redirect('/clipping')
    else:
        # 请求不是 POST，表明用户正在访问注册页面，展示一个空的注册表单给用户
        form = UserCreationForm()

    # 渲染模板
    # 如果用户正在访问注册页面，则渲染的是一个空的注册表单
    # 如果用户通过表单提交注册信息，但是数据验证不合法，则渲染的是一个带有错误信息的表单
    return render(request, 'register.html', context={'form': form, 'title': '用户注册'})

@csrf_exempt
def upload_clipping(request):
    if request.user.id is None:
        return HttpResponse("nouser")

    # if upload_file():
    #     locale.setlocale(locale.LC_ALL, 'zh_CN')
    #     rfile = open(file_name, 'r', encoding="utf-8-sig")
    #     count = 0
    #     flag = True
    #     clipping = {}
    #     book = {}
    #
    #     for line in rfile.readlines():
    #         if line == "==========\n":
    #             continue
    #         else:
    #             count += 1
    #             line = line.strip('\n')  # delete '\n'
    #             if count % 4 == 1:
    #                 pattern = "[\ufeff]*(.*) \((.*)\)"
    #                 matchObj = re.match(pattern, line)
    #                 try:
    #                     name = matchObj.group(1)
    #                     # 去除书名后的备注
    #                     index = -1
    #                     if '（' in name:
    #                         index = name.index('（')
    #                     elif '(' in name:
    #                         index = name.index('(')
    #                     if index != -1:
    #                         book['name'] = name[:index]
    #                     else:
    #                         book['name'] = name
    #                     book['author'] = matchObj.group(2)
    #                 except:
    #                     print(line + "匹配错误")
    #                     flag = False
    #             elif count % 4 == 2:
    #                 pattern = "- 您在(.*)位置 (.*)的标注 \| 添加于 (.*)"
    #                 matchObj = re.match(pattern, line)
    #                 try:
    #                     clipping['location'] = matchObj.group(2).rstrip('）')
    #                     clipping['date'] = datetime.strptime(matchObj.group(3), "%Y年%m月%d日%A %p%I:%M:%S")
    #                 except:
    #                     print(line + "匹配错误")
    #                     flag = False
    #             elif count % 4 == 3:
    #                 continue
    #             elif count % 4 == 0:
    #                 clipping['content'] = line
    #                 if flag:
    #                     book_tmp = Book.objects.get_or_create(book_name=book['name'], author=book['author'])
    #                     # clip = Clipping.objects.get_or_create(content=clipping['content'], book_name=clipping['name'], location=clipping['location'])
    #                     # 有隐患，同一位置后面上传的用户会把前面用户的内容替换掉，当前无法解决此问题
    #                     clip = Clipping.objects.update_or_create(book_id=book_tmp[0].id, location=clipping['location'], defaults={'content': line})
    #                     User_Clipping.objects.update_or_create(user_id=request.user.id, clipping_id=clip[0].id, defaults={'time': clipping['date']})
    #                 flag = True
    #     print(clipping)
    #     return HttpResponse('success')
    # else:
    #     return HttpResponse('error')

    if upload_file(request):
        locale.setlocale(locale.LC_ALL, 'zh_CN')
        rfile = open('./upload_file/' + file_name, 'r', encoding="utf-8-sig")
        i = count = 0
        flag = True
        clipping = {}
        book = {}

        lines = rfile.readlines()
        while i < len(lines):
            line = lines[i].strip('\n')  # delete '\n'
            if count % 5 == 0:  # 标题
                pattern = "[\ufeff]*(.*) \((.*)\)"
                matchObj = re.match(pattern, line)
                try:
                    name = matchObj.group(1)
                    # 去除书名后的备注
                    index = -1
                    if '（' in name:
                        index = name.index('（')
                    elif '(' in name:
                        index = name.index('(')
                    if index != -1:
                        book['name'] = name[:index]
                    else:
                        book['name'] = name
                    book['author'] = matchObj.group(2)
                except:
                    print(line + " 匹配错误")
                    flag = False
            elif count % 5 == 1:  # 位置
                pattern = "- 您在(.*)位置 (.*)的标注 \| 添加于 (.*)"
                matchObj = re.match(pattern, line)
                try:
                    clipping['location'] = matchObj.group(2).rstrip('）')
                    clipping['date'] = datetime.strptime(matchObj.group(3), "%Y年%m月%d日%A %p%I:%M:%S")
                except:
                    print(line + " 匹配错误")
                    flag = False
            elif count % 5 == 2:  # 空白行
                i += 1
                count += 1
                continue
            elif count % 5 == 3:  # 内容
                clipping['content'] = line
                for j in range(i+1, len(lines)):
                    if lines[j] == "==========\n":
                        break
                    clipping['content'] += '\n' + lines[j].strip('\n')
                i = j
                count = 4
                if flag:
                    # print(clipping)
                    book_tmp = Book.objects.get_or_create(book_name=book['name'], defaults={'author': book['author']})
                    # clip = Clipping.objects.get_or_create(content=clipping['content'], book_name=clipping['name'], location=clipping['location'])
                    # 有隐患，同一位置后面上传的用户会把前面用户的内容替换掉，当前无法解决此问题
                    clip = Clipping.objects.update_or_create(book_id=book_tmp[0].id, location=clipping['location'], defaults={'content': clipping['content']})
                    User_Clipping.objects.update_or_create(user_id=request.user.id, clipping_id=clip[0].id, defaults={'time': clipping['date']})
                flag = True
            elif count % 5 == 4:  # ==========\n
                i += 1
                count += 1
                continue
            i += 1
            count += 1
        return HttpResponse('success')
    else:
        return HttpResponse('error')

@login_required
@csrf_exempt
def upload_img(request):
    result = {}
    # 百度OCR SDK
    APP_ID = '15237015'
    API_KEY = 'QIVHjXVrZGq8IjSypyERPukB'
    SECRET_KEY = 'lOMPmpyVyeCdB5SbLxAGK8c8srrFUDbl'

    client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    if upload_file(request):
        # 图片路径
        file_path = './upload_file/' + file_name
        # 可选参数
        options = {}
        options["language_type"] = "CHN_ENG"
        options["detect_direction"] = "true"
        options["detect_language"] = "true"
        options["probability"] = "false"
        words_result = client.basicGeneral(get_file_content(file_path), options)
        if "error_code" in words_result:
            result = {"success": False, "type": 2} # 1为上传错误，2为解析错误
            print("OCR识别错误，错误原因为：" + words_result['error_msg'])
        else:
            words_result = words_result['words_result']
            content = ""
            for item in words_result:
                content += item['words']
            result = {"success": True, "content": content}
    else:
        result = {"success": False, "type": 1}
    return HttpResponse(json.dumps(result), content_type="application/json")

@login_required
def overview(request):
    if request.method == "POST":
        keyword = request.POST.get("keyword")
        clipping_list = User_Clipping.objects\
            .filter(Q(user_id=request.user.id),
                    Q(clipping__content__contains=keyword) | Q(clipping__book__book_name__contains=keyword))\
            .order_by("-time")\
            .values('time', 'clipping__content', 'clipping__location','clipping__book__book_name',
                    'clipping__book__author', 'clipping__book_id', 'clipping_id')
    else:
        clipping_list = User_Clipping.objects\
            .filter(user_id=request.user.id)\
            .order_by("-time")\
            .values('time', 'clipping__content', 'clipping__location','clipping__book__book_name',
                    'clipping__book__author', 'clipping__book_id', 'clipping_id')
    paginator = Paginator(clipping_list, 30)
    page = request.GET.get('page')
    clippings = paginator.get_page(page)

    author_book = {}
    for clipping in clipping_list:
        author = clipping['clipping__book__author']
        book_id = clipping['clipping__book_id']
        book_name = clipping['clipping__book__book_name']
        if author not in author_book:
            author_book[author] = []
        if [book_id, book_name] not in author_book[author]:
            author_book[author].append([book_id, book_name])

    context = {'clippings': clippings, 'author_book': author_book, 'title': '总览'}
    return render(request, 'clipping_overview.html', context)

@login_required
def overview_by_book(request, id):
    # 得到全部文摘
    clipping_all = User_Clipping.objects\
        .filter(user_id=request.user.id)\
        .values('time', 'clipping__content', 'clipping__location','clipping__book__book_name',
                'clipping__book__author', 'clipping__book_id', 'clipping_id')

    author_book = {}
    clipping_book = []
    for clipping in clipping_all:
        author = clipping['clipping__book__author']
        book_id = clipping['clipping__book_id']
        book_name = clipping['clipping__book__book_name']
        # 得到对应书籍的书摘数据
        if book_id == id:
            clipping_book.append(clipping)
            author_active = author
        # 得到侧边栏数据
        if author not in author_book:
            author_book[author] = []
        if [book_id, book_name] not in author_book[author]:
            author_book[author].append([book_id, book_name])

    # 分页
    paginator = Paginator(clipping_book, 10)
    page = request.GET.get('page')
    clippings = paginator.get_page(page)

    context = {'clippings': clippings, 'author_book': author_book, 'title': '总览', 'author_active': author_active}
    return render(request, 'clipping_overview.html', context)

@login_required
def book(request):
    book_list = User_Clipping.objects\
        .filter(user_id=request.user.id)\
        .values('clipping__book__book_name', 'clipping__book__author', 'clipping__book_id', 'clipping__book__ASIN').distinct()
    for book in book_list:
        book_name = book['clipping__book__book_name']
        if book['clipping__book__ASIN']:
            ASIN = book['clipping__book__ASIN']
        else:
            ASIN = get_ASIN(book_name)
            Book.objects.filter(id=book['clipping__book_id']).update(ASIN=ASIN)
        book['img_backup'] = "http://z2-ec2.images-amazon.com/images/P/%s.jpg" % ASIN
        book['img'] = "http://s3.cn-north-1.amazonaws.com.cn/sitbweb-cn/content/%s/images/cover.jpg" % ASIN
    context = {'book_list': book_list, 'title': '书籍库'}
    return render(request, 'book.html', context)

@login_required
def view_by_book(request, book_id):
    clipping_list = User_Clipping.objects\
        .filter(user_id=request.user.id, clipping__book_id=book_id)\
        .values('time', 'clipping__content', 'clipping__location','clipping__book__book_name',
                'clipping__book__author', 'clipping_id')
    paginator = Paginator(clipping_list, 10)
    page = request.GET.get('page')
    clippings = paginator.get_page(page)

    book_info = model_to_dict(Book.objects.get(id=book_id))

    # get book image
    ASIN = book_info['ASIN']
    book_info['img_backup'] = "http://z2-ec2.images-amazon.com/images/P/%s.jpg" % ASIN
    book_info['img'] = "http://s3.cn-north-1.amazonaws.com.cn/sitbweb-cn/content/%s/images/cover.jpg" % ASIN

    # get book summary
    url = "https://api.douban.com/v2/book/search?q=" + book_info['book_name']
    data = requests.get(url=url, headers=get_header()).text
    json_data = json.loads(data)
    book_info['summary'] = json_data['books'][0]['summary']

    # get book tags
    book_info['tags'] = []
    for item in json_data['books'][0]['tags'][:3]:
        book_info['tags'].append(item['name'])

    context = {'clippings': clippings, 'title': '书籍库', 'book_info': book_info}
    return render(request, 'clipping_book.html', context)

@login_required
def export_clipping(request, clipping_id):
    clipping = Clipping.objects.filter(id=clipping_id).values('content', 'book__book_name', 'book__ASIN')[0]
    ASIN = clipping['book__ASIN']
    img_url = [
        "http://s3.cn-north-1.amazonaws.com.cn/sitbweb-cn/content/%s/images/cover.jpg" % ASIN,
        "http://z2-ec2.images-amazon.com/images/P/%s.jpg" % ASIN
    ]
    content = clipping['content']
    # 每25个字插入一个换行符，以适应分享图片的生成
    content = '\n'.join(content[i:i+25] for i in range(0,len(content),25))


    # Img('upload_file/').save2(clipping['book__book_name'], content, '', clipping_id)
    Img('upload_file/').save3(clipping['book__book_name'], content, img_url, clipping_id)
    file=open('upload_file/' + str(clipping_id) + '.png','rb')
    response = HttpResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']='attachment;filename="clipping.png"'
    return response

@login_required
def add_clipping(request):
    book_name = request.POST.get('book_name').strip()
    author = request.POST.get('author').strip()
    content = request.POST.get('content').strip()
    position = request.POST.get('position').strip()
    add_time = datetime.now()

    try:
        book = Book.objects.get_or_create(book_name=book_name, defaults={'author': author})
        clip = Clipping.objects.update_or_create(book_id=book[0].id, location=position,
                                                 defaults={'content': content})
        User_Clipping.objects.update_or_create(user_id=request.user.id, clipping_id=clip[0].id,
                                               defaults={'time': add_time})
        result = {'success': True}
    except Exception as e:
        result = {'success': False}
        print(repr(e))
    return HttpResponse(json.dumps(result), content_type="application/json")

@login_required
def del_clipping(request):
    clipping_id = request.POST.get('id')
    try:
        User_Clipping.objects.filter(clipping_id=clipping_id, user_id=request.user.id).delete()
        result = {'success': True}
    except:
        print("删除文摘失败，id为" + str(clipping_id))
        result = {'success': False}
    return HttpResponse(json.dumps(result), content_type="application/json")

@login_required
def author(request):
    author_list = User_Clipping.objects\
        .filter(user_id=request.user.id)\
        .values('clipping__book__author').distinct()
    context = {'author_list': author_list, 'title': '作者库'}
    return render(request, 'author.html', context)

@login_required
def statistics(request):
    context = {'title': '阅读统计'}
    return render(request, 'statistics.html', context)

def upload_file(request):
    if request.method == "POST":  # 请求方法为POST时，进行处理
        myFile = request.FILES.get("file", None)  # 获取上传的文件，如果没有文件，则默认为None
        if not myFile:
            return False
        else:
            global file_name
            file_name = myFile.name
            destination = open('./upload_file/' + myFile.name, 'wb+')  # 打开特定的文件进行二进制的写操作
            for chunk in myFile.chunks():  # 分块写入文件
                destination.write(chunk)
            destination.close()
            return True

def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

def get_ua():
    with open("./static/UA_list.txt") as fileua:
        uas = fileua.readlines()
        import random
        cnt = random.randint(0,len(uas)-1)
        return uas[cnt].replace("\n","")

def get_header():
    header = {
        'Referer': 'https://www.amazon.cn/',
        'User-agent': get_ua(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accetp-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8'
    }
    return header

def get_ASIN(book_name):
    header = get_header()
    with requests.session() as s:
        req = s.get('https://www.amazon.cn/', headers=header)
        cookie = requests.utils.dict_from_cookiejar(req.cookies)
    url = "https://www.amazon.cn/s/ref=nb_sb_noss?__mk_zh_CN=亚马逊网站&url=search-alias%3Ddigital-text&field-keywords=" + book_name
    data = requests.get(url=url, cookies=cookie, headers=header)
    data.encoding = 'utf-8'
    s = etree.HTML(data.text)
    asin = s.xpath('//*[@id="result_0"]/@data-asin')
    if len(asin) == 0:
        return None
    return asin[0]

def get_clipping_num_per_month(request, year):
    MONTHS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
    nums = []
    result = {}
    try:
        for month in MONTHS:
            clipping_num = User_Clipping.objects\
                .filter(user_id=request.user.id, time__year=year, time__month=month).count()
            nums.append(clipping_num)
        result['success'] = True
        result['data'] = nums
    except:
        result['success'] = False

    return HttpResponse(json.dumps(result))