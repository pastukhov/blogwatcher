#!/usr/bin/env python3
"""
Скрипт генерации дайджестов новостей для BlogWatcher.

Поддерживает:
- Ежедневные дайджесты в 14:00, 19:00, 22:00
- Топ-10 новостей за неделю (в субботу 9:00)
- Умную фильтрацию новых статей между дайджестами
- Отслеживание важности и популярности новостей
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import urllib.parse


def get_article_fingerprint(article):
    """Генерирует уникальный 'отпечаток' статьи для отслеживания изменений."""
    # Используем заголовок и URL как уникальный идентификатор
    unique_data = f"{article.get('title', '')}||{article.get('url', '')}"
    return hashlib.md5(unique_data.encode()).hexdigest()


def load_tracking_state():
    """Загружает состояние отслеживания статей (какие уже были в дайджестах)."""
    state_dir = Path.home() / ".hermes" / "blogwatcher_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    tracking_file = state_dir / "tracked_articles.json"
    
    if not tracking_file.exists():
        return {"count": 0, "articles": []}
    
    try:
        with open(tracking_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"count": 0, "articles": []}


def save_tracking_state(data):
    """Сохраняет состояние отслеживания."""
    state_dir = Path.home() / ".hermes" / "blogwatcher_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    tracking_file = state_dir / "tracked_articles.json"
    
    with open(tracking_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def calculate_article_score(article):
    """Вычисляет 'важность' новости по нескольким факторам."""
    score = 0
    
    # Свежесть - чем новее, тем важнее
    try:
        published = article.get('published', '')
        if published:
            pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
            hours_ago = (datetime.now() - pub_dt).total_seconds() / 3600
            score += max(10, 50 - hours_ago)  # Меньше часов - выше рейтинг
    except:
        pass
    
    # Длина заголовка - более длинные обычно важнее
    title = article.get('title', '')
    if len(title) > 40:
        score += 5
    elif len(title) > 20:
        score += 2
    
    return round(score, 1)


def filter_new_articles(all_articles):
    """Фильтрует только новые статьи, появившиеся после последнего дайджеста."""
    tracking = load_tracking_state()
    
    new_articles = []
    added_count = 0
    
    for article in all_articles:
        fingerprint = get_article_fingerprint(article)
        
        # Проверка, была ли эта статья раньше
        was_tracked = False
        if fingerprint in [a['fingerprint'] for a in tracking['articles']]:
            was_tracked = True
        
        if not was_tracked and article.get('is_read', False):
            new_articles.append({
                'article': article,
                'score': calculate_article_score(article),
                'rank': added_count + 1
            })
            tracking['articles'].append({
                'fingerprint': fingerprint,
                'title': article.get('title', ''),
                'url': article.get('url', '')
            })
            tracking['count'] = len(tracking['articles'])
            
            saved_tracking = save_tracking_state(tracking)
            added_count += 1
    
    return new_articles


def generate_daily_digest(title, articles):
    """Загружает последний timestamp дайджеста."""
    state_dir = Path.home() / ".hermes" / "blogwatcher_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    last_digest_file = state_dir / "last_digest_timestamp.txt"
    
    if not last_digest_file.exists():
        last_digest_file.write_text(str(int(datetime.now().timestamp())))
    
    return int(last_digest_file.read_text().strip())


def save_blogwatcher_state(timestamp):
    """Сохраняет timestamp текущего дайджеста."""
    state_dir = Path.home() / ".hermes" / "blogwatcher_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    last_digest_file = state_dir / "last_digest_timestamp.txt"
    last_digest_file.write_text(str(timestamp))


def fetch_articles_json(since_timestamp):
    """Загружает статьи через blogwatcher в JSON формате."""
    import subprocess
    
    # Вычисляем timestamp для загрузки (чуть раньше указанного)
    offset = 300  # 5 минут назад
    actual_since = since_timestamp - offset
    
    try:
        result = subprocess.run(
            [
                'blogwatcher', 'articles',
                '-o', 'json',
                f'--since={actual_since}'
            ],
            capture_output=True,
            text=True,
            cwd=Path.home() / "repos" / "blogwatcher"
        )
        
        if result.returncode != 0:
            print(f"Ошибка при загрузке статей: {result.stderr}")
            return []
        
        articles = json.loads(result.stdout)
        # Фильтруем только новые, не учтённые ранее
        new_articles = filter_new_articles(articles)
        return new_articles
    except FileNotFoundError:
        print("⚠ blogwatcher не найден в PATH")
        print("Подсказка: добавьте путь к bin-директории в PATH или используйте полный путь")
        return []
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        print(result.stdout[:500] if result.stdout else "Нет вывода")
        return []


def load_blogwatcher_state():
    """Загружает последний timestamp дайджеста."""
    state_dir = Path.home() / ".hermes" / "blogwatcher_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    last_digest_file = state_dir / "last_digest_timestamp.txt"
    
    if not last_digest_file.exists():
        last_digest_file.write_text(str(int(datetime.now().timestamp())))
    
    timestamp_str = last_digest_file.read_text().strip()
    return int(float(timestamp_str))  # Обработка с плавающей точкой


def load_tracking_state():
    """Загружает состояние отслеживания статей (какие уже были в дайджестах)."""
    state_dir = Path.home() / ".hermes" / "blogwatcher_state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    tracking_file = state_dir / "tracked_articles.json"
    
    if not tracking_file.exists():
        return {"count": 0, "articles": []}
    
    try:
        with open(tracking_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"count": 0, "articles": []}


def format_datetime(dt, time_only=False):
    """Форматирует datetime в понятный вид."""
    if time_only:
        return dt.strftime("%H:%M")
    return dt.strftime("%d.%m.%Y %H:%M")


def is_weekend():
    """Проверяет, выходной ли день (суббота или воскресенье)."""
    today = datetime.now()
    return today.weekday() >= 5


def generate_daily_digest(title, articles):
    """Генерирует ежедневный дайджест."""
    output = []
    output.append(f"# {title}")
    output.append("")
    output.append(f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    output.append(f"**Новостей:** {len(articles)}")
    output.append("")
    
    # Группировка по источникам
    by_source = {}
    for article in articles:
        source = article.get('blog', 'Неизвестный источник')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(article)
    
    if not by_source:
        output.append("📭 Нет новых новостей в этот момент.")
        return "\n".join(output)
    
    for source, articles_list in by_source.items():
        output.append(f"## {source}")
        output.append("")
        
        # Сортировка по дате публикации (новые первыми)
        sorted_articles = sorted(articles_list, key=lambda x: x.get('published', ''), reverse=True)
        
        for article in sorted_articles:
            title = article.get('title', 'Без заголовка')
            url = article.get('url', '#')
            published = article.get('published', 'Неизвестно')
            
            # Форматируем дату публикации
            try:
                pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                formatted_pub = pub_dt.strftime('%d.%m.%Y %H:%M')
            except:
                formatted_pub = published
            
            output.append(f"- [{title}]({url})")
            output.append(f"  📅 Опубликовано: {formatted_pub}")
            output.append("")
    
    return "\n".join(output)


def generate_top10_digest(title, articles):
    """Генерирует топ-10 новостей (с учётом рейтингов)."""
    output = []
    output.append(f"# 🏆 Топ-10 лучших новостей")
    output.append("")
    output.append(f"**Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    if not articles:
        output.append("Нет новых новостей.")
        return "\n".join(output)
    
    # Берем топ-10 (или меньше, если новостей меньше 10)
    top_articles = articles[:10]
    output.append(f"### Топ-10 ({min(len(top_articles), 10)})")
    output.append("")
    
    for item in top_articles:
        article = item['article']
        rank = item['rank']
        title = article.get('title', 'Без заголовка')
        url = article.get('url', '#')
        blog = article.get('blog', 'Неизвестный источник')
        published = article.get('published', 'Неизвестно')
        
        try:
            pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
            formatted_pub = pub_dt.strftime('%d.%m %H:%M')
        except:
            formatted_pub = published
        
        output.append(f"### {rank}. {title}")
        output.append("")
        output.append(f"📰 **{blog}**")
        output.append(f"📅 **{formatted_pub}**")
        output.append(f"⚡ Рейтинг: {item['score']}/100")
        output.append("")
        output.append(f"[{title}]({url})")
        output.append("")
    
    return "\n".join(output)


def generate_weekly_digest(title, articles):
    start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())
    end_of_week = start_of_week + timedelta(days=7)
    
    output.append(f"# 📰 Еженедельный дайджест новостей")
    output.append("")
    output.append(f"**Неделя:** {start_of_week.strftime('%d.%m')}-{end_of_week.strftime('%d.%m')}")
    output.append(f"**Дата генерации:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    output.append(f"**Новостей:** {len(articles)}")
    output.append("")
    
    # Группировка по источникам
    by_source = {}
    for article in articles:
        source = article.get('blog', 'Неизвестный источник')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(article)
    
    for source, articles_list in sorted(by_source.items()):
        output.append(f"## {source}")
        output.append("")
        
        # Сортировка по дате (новые первыми)
        sorted_articles = sorted(articles_list, key=lambda x: x.get('published', ''), reverse=True)
        
        for article in sorted_articles:
            title = article.get('title', 'Без заголовка')
            url = article.get('url', '#')
            published = article.get('published', 'Неизвестно')
            
            try:
                pub_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                formatted_pub = pub_dt.strftime('%d.%m %H:%M')
            except:
                formatted_pub = published
            
            output.append(f"- [{title}]({url}) — {formatted_pub}")
        
        output.append("")
    
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(description='Генерация дайджестов новостей')
    parser.add_argument('--type', '-t', choices=['daily', 'top10', 'weekly'],
                       default='daily', help='Тип дайджеста: daily или weekly')
    parser.add_argument('--time', required=True, type=int,
                       help='Час для генерации (для определения типа дайджеста)')
    parser.add_argument('--output', '-o', default=None,
                       help='Файл вывода (если не указан, выводит в stdout)')
    parser.add_argument('--preview', action='store_true',
                       help='Показать предпросмотр без сохранения')
    
    args = parser.parse_args()
    
    # Определяем тип дайджеста по времени и дню недели
    current_hour = args.time
    
    # Проверяем день недели
    today = datetime.now()
    is_weekend_today = today.weekday() >= 5  # суббота или воскресенье
    
    # В выходные (суббота) в 9:00 - недельный дайджест, иначе ежедневный
    if current_hour == 9 and is_weekend_today:
        title = "🏆 Топ-10 лучших новостей за неделю!"
        articles = fetch_articles_json(load_blogwatcher_state())
        output_text = generate_weekly_digest(title, articles)
    else:
        # Ежедневные дайджесты
        if current_hour == 14:
            title_prefix = "☀️ Дневной дайджест"
        elif current_hour == 19:
            title_prefix = "🌆 Вечерний дайджест"
        else:  # 22:00
            title_prefix = "🌙 Ночной дайджест"
        
        title = f"{title_prefix} от {today.strftime('%d.%m')}"
        articles = fetch_articles_json(load_blogwatcher_state())
        output_text = generate_daily_digest(title, articles)
    
    # Сохраняем timestamp текущего дайджеста
    save_blogwatcher_state(datetime.now().timestamp())
    
    # Вывод или сохранение
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"✓ Дайджест сохранён в {args.output}")
    else:
        print(output_text)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
