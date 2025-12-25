-- =====================
-- ENUM TYPES (Implied via Application Logic)
-- =====================
-- UserRole: 'USER', 'ADMIN'
-- UserStatus: 'ACTIVE', 'BLOCKED', 'DELETED'

-- =====================
-- USERS
-- =====================
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  nickname VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'USER',
  status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- =====================
-- GENRES
-- =====================
CREATE TABLE genres (
  id SERIAL PRIMARY KEY,
  tmdb_genre_id INTEGER NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMP
);

CREATE INDEX idx_genres_tmdb_id ON genres(tmdb_genre_id);

-- =====================
-- CONTENTS
-- =====================
CREATE TABLE contents (
  id SERIAL PRIMARY KEY,
  tmdb_id INTEGER NOT NULL UNIQUE,
  title VARCHAR(255) NOT NULL,
  release_date DATE,
  runtime_minutes INTEGER,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMP
);

CREATE INDEX idx_contents_tmdb_id ON contents(tmdb_id);
CREATE INDEX idx_contents_title ON contents(title);

-- =====================
-- CONTENT_GENRES (N:M Link)
-- =====================
CREATE TABLE content_genres (
  content_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL,
  PRIMARY KEY (content_id, genre_id),
  CONSTRAINT fk_cg_content FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
  CONSTRAINT fk_cg_genre FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
);

-- =====================
-- REVIEWS
-- =====================
CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL,
  content_id INTEGER NOT NULL,
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
  comment TEXT NOT NULL,
  like_count INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  
  CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_reviews_content FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE
);

-- =====================
-- REVIEW_LIKES
-- =====================
CREATE TABLE review_likes (
  user_id INTEGER NOT NULL,
  review_id INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, review_id),
  
  CONSTRAINT fk_rl_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_rl_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
);

-- =====================
-- BOOKMARKS
-- =====================
CREATE TABLE bookmarks (
  user_id INTEGER NOT NULL,
  content_id INTEGER NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, content_id),
  
  CONSTRAINT fk_bm_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_bm_content FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE
);