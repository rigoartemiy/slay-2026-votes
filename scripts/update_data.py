import json,re,sys,time,unicodedata
from datetime import datetime,timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data.json'; URL='https://t.me/s/slay_awards'; CATS=['SLAY King','SLAY Queen','Лучший CS-стример','Лучший Dota-стример','Лучший multigaming-стример','NEXT GEN','Лучший IRL-стример','Проект года на Twitch','Аудитория года','Пара года','Завоз года','Трек года','Косплеер года','Ютубер года','Лучший Minecraft-стример','Человек-мем года']
EM=re.compile('[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D\u20E3]')
def clean(s):return re.sub(r'\s+',' ',EM.sub('',unicodedata.normalize('NFC',s))).strip(' \t\r\n;,.')
def canon(c,v):
 if c in ('Проект года на Twitch','Завоз года'):
  s=clean(v).strip('«»“”"\'').replace('Bосхождение','Восхождение').replace('EgorikShkred','Егорик')
  if s.casefold()=='восхождение на пик ленина':return 'Восхождение на пик Ленина'
  if s.casefold()=='егорик разрушает комнаты стримеров':return 'Егорик разрушает комнаты стримеров'
  if s.casefold() in ('медиа класико','betboom медиа класико'):return 'BetBoom Медиа Класико'
  return s
 if c=='Пара года':
  s=clean(v).replace('Диор Армани','Dior Armani');p=re.split(r'\s*(?:и|&)\s*',s)
  return ' & '.join(sorted([x.strip() for x in p],key=str.casefold)) if len(p)==2 else s
 if c=='Трек года':
  q=re.findall(r'[«“\"](.*?)[»”\"]',v); title=clean(q[-1] if q else v); before=v[:v.rfind(q[-1])] if q else '';after=v[v.rfind(q[-1])+len(q[-1])+1:] if q else '';m=re.search(r'от\s+(.+)$',after);artist=clean(m.group(1)) if m else clean(before.split('—')[0]).strip(' —');return f'{title} — {artist}' if artist else title
 return clean(v)
def extract(text):
 out={}
 for chunk in text.split('•')[1:]:
  m=re.match(r'\s*(.+?)\s*—\s*(.*)$',chunk,re.S)
  if not m:continue
  c=m.group(1).strip();v=m.group(2).strip()
  if c not in CATS:continue
  v=re.sub(r'🤩\s*Проголосовать.*$','',v,flags=re.S);v=re.sub(r'🤩\s*Купить билет.*$','',v,flags=re.S);v=v.strip().rstrip(';').strip()
  if v and 'не проголосовал' not in v.casefold():out[c]=canon(c,v)
 return out
def author(text):
 triggers=r'(?:один из первых|показала|показал|продолжает|подключился|поделился|проголосовал|выбрала|распределил|отдала|назвал|не остался|определился|присоединилась|сделал|продемонстрировал|не изменяет|решил|голосует|осталась|поддержала|наблюдает|оставил|пообещал)'
 m=re.search(r'([^\W_][\w.-]*)\s+'+triggers,text,re.I|re.UNICODE)
 return m.group(1) if m else 'Автор не указан'
def main():
 d=json.loads(DATA.read_text(encoding='utf-8'))
 def in_scope(ballot):
  date=str(ballot.get('date',''))
  if len(date)==10 and date[2]=='.' and date[5]=='.':
   date=date[6:10]+'-'+date[3:5]+'-'+date[:2]
  return date>='2026-11-15'
 known_authors={'9443':'DanilaGorilla','9448':'Exile','9474':'DmitryLixxx'}
 existing={str(x['id']):x for x in d.get('ballots',[]) if in_scope(x)}
 before=min([int(x['id']) for x in existing.values()] or [999999])
 url=URL
 seen=set()
 for _ in range(60):
  resp=requests.get(url,timeout=30,headers={'User-Agent':'Mozilla/5.0'})
  resp.raise_for_status()
  soup=BeautifulSoup(resp.text,'html.parser')
  wraps=soup.select('.tgme_widget_message_wrap')
  ids=[]
  older=False
  for w in wraps:
   msg=w.select_one('.tgme_widget_message')
   body=w.select_one('.tgme_widget_message_text')
   tm=w.select_one('time[datetime]')
   if not msg or not body:
    continue
   post=msg.get('data-post','')
   mid=post.rsplit('/',1)[-1] if '/' in post else ''
   if not mid.isdigit():
    continue
   ids.append(int(mid))
   seen.add(mid)
   date=tm.get('datetime','') if tm else ''
   text=body.get_text(' ',strip=True)
   votes=extract(text)
   if len(votes)>=8 and date and date[:10]>='2026-11-15':
    voter=known_authors.get(mid) or author(text)
    existing[mid]={'id':mid,'author':voter,'date':date[:10],'publishedAt':date,'postUrl':'https://t.me/slay_awards/'+mid,'votes':votes}
   if date and date[:10]<'2026-11-15':
    older=True
  if older or not ids:
   break
  nxt=min(ids)
  if nxt<=before:
   break
  url=URL+'?before='+str(nxt)
 for ballot in existing.values():
  mid=str(ballot.get('id',''))
  if mid in known_authors:
   ballot['author']=known_authors[mid]
  ballot['postUrl']='https://t.me/slay_awards/'+mid
  ballot['votes']={category:canon(category,value) for category,value in ballot.get('votes',{}).items()}
 d['ballots']=sorted(existing.values(),key=lambda x:int(x['id']))
 d['updatedAt']=datetime.now(timezone.utc).isoformat(timespec='seconds')
 DATA.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Saved '+str(len(d['ballots']))+' ballots; '+str(len(seen))+' Telegram posts checked')
if __name__=='__main__':
 main()
