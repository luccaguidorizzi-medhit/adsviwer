import urllib.request
import json
import urllib.parse
import time
from urllib.error import HTTPError

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://adstransparency.google.com',
    'Referer': 'https://adstransparency.google.com/?region=BR'
}

def search_creatives(domain=None, advertiser_id=None):
    url = 'https://adstransparency.google.com/anji/_/rpc/SearchService/SearchCreatives?authuser='
    criterion = {'8': [2076]}  # Region Brazil
    if domain:
        criterion['12'] = {'1': domain, '2': True}
    if advertiser_id:
        criterion['13'] = {'1': [advertiser_id]}
    
    payload = {
        '2': 10,
        '3': criterion,
        '7': {'1': 1, '2': 0, '3': 2250}
    }
    body = 'f.req=' + urllib.parse.quote(json.dumps(payload))
    req = urllib.request.Request(url, data=body.encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            creatives = data.get('1', [])
            total_hint = data.get('4', len(creatives))
            adv_name = creatives[0].get('12', '') if creatives else ''
            return len(creatives), total_hint, adv_name
    except Exception as e:
        return 0, 0, f'Error: {e}'

def search_suggestions(query):
    url = 'https://adstransparency.google.com/anji/_/rpc/SearchService/SearchSuggestions?authuser='
    payload = {'1': query, '2': 10, '3': 10, '5': {'1': 1}}
    body = 'f.req=' + urllib.parse.quote(json.dumps(payload))
    req = urllib.request.Request(url, data=body.encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data.get('1', [])
            matches = []
            for it in items:
                if '1' in it and '2' in it['1']:
                    matches.append((it['1'].get('1'), it['1'].get('2'), it['1'].get('3')))
                elif '2' in it and '1' in it['2']:
                    matches.append((it['2'].get('1'), None, None))
            return matches
    except Exception as e:
        return []

competitors = [
    {'name': 'Mundo Revalida (NÓS)', 'domains': ['mundorevalida.com.br'], 'query': 'Mundo Revalida'},
    {'name': 'Hardwork Revalida', 'domains': ['hardworkmedicina.com.br', 'home.hardworkmedicina.com.br'], 'query': 'Hardwork'},
    {'name': 'Estratégia MED', 'domains': ['estrategia.com', 'med.estrategia.com'], 'query': 'Estrategia'},
    {'name': 'Medtwins Revalida', 'domains': ['medtwins.com.br'], 'query': 'Medtwins'},
    {'name': 'Medcel (Afya)', 'domains': ['medcel.com.br'], 'query': 'Medcel'},
    {'name': 'Medgrupo Revalida', 'domains': ['medgrupo.com.br'], 'query': 'Medgrupo'},
    {'name': 'MedCof Revalida', 'domains': ['grupomedcof.com.br', 'revalida.grupomedcof.com.br'], 'query': 'Medcof'},
    {'name': 'Bastidores do Revalida', 'domains': ['bastidoresdorevalida.com.br'], 'query': 'Bastidores do Revalida'},
    {'name': 'Aristo Revalida', 'domains': ['aristo.com.br'], 'query': 'Aristo'},
    {'name': 'Medway Revalida', 'domains': ['medway.com.br'], 'query': 'Medway'},
    {'name': 'Sanar Revalida', 'domains': ['sanarmed.com', 'sanar.com'], 'query': 'Sanar'},
    {'name': 'VerboMed Revalida', 'domains': ['verbomed.com.br'], 'query': 'VerboMed'},
    {'name': 'Pense Revalida', 'domains': ['penserevalida.com.br'], 'query': 'Pense Revalida'},
    {'name': 'Revalideii', 'domains': ['revalideii.com.br'], 'query': 'Revalideii'},
    {'name': 'Revalida 360', 'domains': ['revalida360.com.br'], 'query': 'Revalida 360'},
    {'name': 'Revmed Mentoria', 'domains': ['revmed.com.br'], 'query': 'Revmed'},
    {'name': 'AlphaMed Revalida', 'domains': ['alphamedrevalida.com.br'], 'query': 'Alphamed'}
]

results = []

for c in competitors:
    c_name = c['name']
    found = False
    details = {'name': c_name, 'active': False, 'ads_count': 0, 'adv_name': '', 'matched_by': '', 'notes': ''}
    
    # 1. Test domains
    for d in c['domains']:
        count, hint, adv = search_creatives(domain=d)
        time.sleep(0.4)
        if count > 0:
            details['active'] = True
            details['ads_count'] = count
            details['adv_name'] = adv
            details['matched_by'] = f'Dominio: {d}'
            details['notes'] = f'Pelo menos {count} anuncios ativos no Brasil (estimativa total: {hint})'
            found = True
            break
            
    # 2. If not found by domain, test suggestions by name
    if not found:
        suggs = search_suggestions(c['query'])
        time.sleep(0.4)
        adv_matches = [s for s in suggs if s[1] and s[1].startswith('AR')]
        for s_name, s_id, s_country in adv_matches:
            count, hint, adv = search_creatives(advertiser_id=s_id)
            time.sleep(0.4)
            if count > 0:
                details['active'] = True
                details['ads_count'] = count
                details['adv_name'] = s_name
                details['matched_by'] = f'Anunciante: {s_name} ({s_id})'
                details['notes'] = f'{count} anuncios ativos no Brasil'
                found = True
                break
                
    if not found:
        details['notes'] = 'Nenhum anuncio ativo encontrado na busca por dominio ou razao social no Google Ads Transparency (BR)'
        
    results.append(details)
    adv_display = details['adv_name'][:30] if details['adv_name'] else 'Nenhum'
    status_str = 'ATIVO' if details['active'] else 'SEM ANUNCIOS'
    print(f"{c_name:25} | {status_str:13} | Anuncios: {details['ads_count']:2} | {adv_display}")

with open('data/google_ads_audit_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('\nAuditoria concluida e salva em data/google_ads_audit_results.json')
