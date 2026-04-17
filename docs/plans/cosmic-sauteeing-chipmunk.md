# Plan: OPML Import

## Context

Пользователь хочет импортировать подписки из Feedly (формат OPML) в BlogWatcher. OPML файл содержит 100+ RSS-подписок с категориями, URL блогов и URL фидов.

## Подход

### 1. Парсер OPML — `internal/opml/opml.go`

Новый пакет для парсинга OPML. Используем стандартный `encoding/xml`.

Структуры:
- `OPML` — корневой элемент
- `Outline` — элемент `<outline>`, может быть категорией (содержит вложенные outline) или фидом (type="rss", имеет xmlUrl/htmlUrl)

Функция `Parse(reader io.Reader) ([]Feed, error)` — возвращает плоский список фидов из всех категорий.

Структура `Feed`:
- `Title` (из `title` или `text`)
- `SiteURL` (из `htmlUrl`)
- `FeedURL` (из `xmlUrl`)

### 2. Метод контроллера — `internal/controller/controller.go`

`ImportOPML(reader io.Reader) (added int, skipped int, err error)`:
- Парсит OPML через `opml.Parse()`
- Для каждого фида вызывает `AddBlog()`, при `BlogAlreadyExistsError` — увеличивает `skipped`
- Возвращает количество добавленных и пропущенных блогов

### 3. CLI команда — `internal/cli/commands.go`

`blogwatcher import <file>` — новая команда:
- Принимает путь к OPML файлу
- Открывает файл, передаёт в контроллер
- Выводит результат: "Imported X blogs, skipped Y duplicates"

### 4. Тесты — `internal/opml/opml_test.go`

Юнит-тесты парсера OPML:
- Парсинг стандартного OPML с категориями
- Пропуск пустых категорий
- Обработка outline без xmlUrl

## Файлы

| Файл | Действие |
|------|----------|
| `internal/opml/opml.go` | Создать — парсер OPML |
| `internal/opml/opml_test.go` | Создать — тесты парсера |
| `internal/controller/controller.go` | Изменить — добавить `ImportOPML()` |
| `internal/cli/commands.go` | Изменить — добавить команду `import` |
| `internal/cli/root.go` | Изменить — зарегистрировать команду |

## Проверка

1. `go test ./...` — все тесты проходят
2. `go run ./cmd/blogwatcher import feedly-opml-*.opml` — импорт проходит успешно
3. `go run ./cmd/blogwatcher blogs` — импортированные блоги отображаются
