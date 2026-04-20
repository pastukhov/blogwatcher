package model

import (
	"encoding/json"
	"time"
)

type Blog struct {
	ID             int64
	Name           string
	URL            string
	FeedURL        string
	ScrapeSelector string
	LastScanned    *time.Time
}

type Article struct {
	// ID - уникальный идентификатор статьи
	ID             int64
	// BlogID - ID блога (для ссылок)
	BlogID         int64
	// Title - заголовок статьи
	Title          string
	// URL - ссылка на статью
	URL            string
	// PublishedDate - дата публикации
	PublishedDate  *time.Time
	// DiscoveredDate - когда статья была найдена
	DiscoveredDate *time.Time
	// IsRead - прочитана или нет
	IsRead         bool
}

func (a *Article) MarshalJSON() ([]byte, error) {
	type Alias Article
	return json.Marshal(struct {
		ID          int64    `json:"id"`
		BlogID      int64    `json:"blog_id"`
		Title       string   `json:"title"`
		URL         string   `json:"url"`
		PublishedAt string   `json:"published_at,omitempty"`
		Read        bool     `json:"read"`
	}{
		ID:          a.ID,
		BlogID:      a.BlogID,
		Title:       a.Title,
		URL:         a.URL,
		PublishedAt: "",
		Read:        a.IsRead,
	})
}


