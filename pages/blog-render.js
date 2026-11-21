(() => {
  'use strict';

  const root = document.getElementById('fluffy-blog');
  const status = document.getElementById('fluffy-blog-status');
  if (!root || !status) return;

  const config = window.FLUFFY_BLOG;
  const settings = config?.settings;
  const categories = new Map(Object.entries(settings?.categories ?? {}));
  const query = new URLSearchParams(window.location.search);
  const postId = query.get('post');
  const requestedTag = query.get('tag');
  const activeTag = categories.has(requestedTag) ? requestedTag : '';
  const assetsBase = new URL('./assets/', document.baseURI).href;

  const dateFormat = new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  });

  let cardNumber = 0;

  function el(tag, className = '', text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function blogUrl(params = {}) {
    const search = new URLSearchParams(params).toString();
    return search ? `./blog.html?${search}` : './blog.html';
  }

  function link(text, href, className) {
    const node = el('a', className, text);
    node.href = href;
    return node;
  }

  function assetUrl(path, folder = '') {
    if (typeof path !== 'string' || !path.startsWith(`assets/${folder}`)) {
      return null;
    }

    try {
      const url = new URL(path, document.baseURI);
      return url.href.startsWith(`${assetsBase}${folder}`) ? url.href : null;
    } catch {
      return null;
    }
  }

  function image(url, alt, onError, lazy = true) {
    const node = el('img');
    node.alt = alt;
    node.decoding = 'async';
    if (lazy) node.loading = 'lazy';
    node.addEventListener('error', onError, { once: true });
    node.src = url;
    return node;
  }

  function authorByline(post, showBio = false) {
    const author = { ...config.author, ...post.author };
    const initials = Array.from(author.name.trim())[0].toUpperCase();

    const byline = el('div', 'blog-author');
    const avatar = el('span', 'blog-avatar', initials);
    avatar.setAttribute('aria-hidden', 'true');

    const avatarUrl = assetUrl(author.avatar, 'avatars/');
    if (avatarUrl) {
      avatar.replaceChildren(image(avatarUrl, '', () => {
        avatar.textContent = initials;
      }));
    }

    const details = el('div');
    details.append(el('strong', 'blog-author-name', author.name));
    if (author.role) details.append(el('span', 'blog-author-role', author.role));
    if (showBio && author.bio) {
      details.append(el('p', 'blog-author-bio', author.bio));
    }

    byline.append(avatar, details);
    return byline;
  }

  function parseDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return null;
    }
    const date = new Date(`${value}T00:00:00Z`);
    return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value
      ? date : null;
  }

  function metadata(post, clickable = false) {
    const row = el('div', clickable ? 'blog-post-meta' : 'blog-card-meta');

    for (const tag of new Set(post.tags)) {
      const label = categories.get(tag);
      if (!label) continue;
      row.append(clickable
        ? link(label, blogUrl({ tag }), 'blog-meta-item')
        : el('span', 'blog-meta-item', label));
    }

    if (post.version) {
      row.append(el('span', 'blog-meta-item blog-meta-item--version', post.version));
    }

    const date = parseDate(post.date);
    if (date) {
      const time = el('time', 'blog-post-date', dateFormat.format(date));
      time.dateTime = post.date;
      row.append(time);
    }

    return row;
  }

  function card(post, featured = false) {
    const item = el('article', featured ? 'blog-entry blog-entry--featured' : 'blog-entry');
    const params = activeTag ? { post: post.id, tag: activeTag } : { post: post.id };
    const cardLink = link('', blogUrl(params), 'blog-card blog-card--no-cover');
    const body = el('div', 'blog-card-body');
    const title = el('h3', 'blog-card-title', post.title);
    title.id = `blog-card-title-${++cardNumber}`;
    cardLink.setAttribute('aria-labelledby', title.id);

    body.append(metadata(post), title);
    if (post.description) body.append(el('p', 'blog-description', post.description));

    const footer = el('div', 'blog-card-footer');
    const arrow = el('span', 'blog-card-arrow', '→');
    arrow.setAttribute('aria-hidden', 'true');
    footer.append(authorByline(post), arrow);
    body.append(footer);

    const coverPath = post.cover === false ? null : [
      post.cover,
      ...post.content.filter(block => block?.type === 'image').map(block => block.src),
    ].map(path => assetUrl(path)).find(Boolean);

    if (coverPath) {
      const media = el('div', 'blog-card-media');
      media.append(image(coverPath, '', () => {
        media.remove();
        cardLink.classList.add('blog-card--no-cover');
      }, !featured));
      cardLink.append(media);
      cardLink.classList.remove('blog-card--no-cover');
    }

    cardLink.append(body);
    item.append(cardLink);
    return item;
  }

  function section(title, posts, featured = false) {
    const node = el('section', 'blog-section');
    const grid = el('div', 'blog-grid');
    for (const post of posts) grid.append(card(post, featured));
    node.append(el('h2', 'blog-section-title', title), grid);
    return node;
  }

  function renderList(posts) {
    document.title = settings.title;

    const intro = el('div', 'blog-intro');
    const title = el('h1');
    title.append(el('span', settings.gradientTitle ? 'blog-title-gradient' : '', settings.title));
    intro.append(title);
    if (settings.description) {
      intro.append(el('p', 'blog-description', settings.description));
    }

    const filters = el('nav', 'blog-filters');
    filters.setAttribute('aria-label', 'Рубрики блога');
    for (const [tag, label] of [['', settings.allLabel], ...categories]) {
      const filter = link(label, tag ? blogUrl({ tag }) : blogUrl(), 'blog-filter');
      if (tag === activeTag) filter.setAttribute('aria-current', 'page');
      filters.append(filter);
    }

    root.append(intro, filters);

    const visible = activeTag ? posts.filter(post => post.tags.includes(activeTag)) : posts;
    if (!visible.length) {
      root.append(el('p', 'blog-empty', activeTag
        ? 'В этой рубрике пока нет записей.'
        : 'В блоге пока нет записей.'));
      return;
    }

    if (activeTag) {
      root.append(section(categories.get(activeTag), visible));
      return;
    }

    const pinned = visible.find(post => post.pinned === true);
    const featured = pinned || visible[0];
    const archive = visible.filter(post => post !== featured);

    root.append(section(pinned ? settings.pinnedLabel : settings.latestLabel, [featured], true));
    if (archive.length) root.append(section(settings.archiveLabel, archive));
  }

  function renderPost(post) {
    const article = el('article', 'blog-post');
    article.append(link(
      `← ${activeTag ? categories.get(activeTag) : settings.allLabel}`,
      activeTag ? blogUrl({ tag: activeTag }) : blogUrl(),
      'blog-back',
    ));
    root.append(article);

    if (!post) {
      article.append(el('h1', '', 'Запись не найдена'));
      document.title = `Запись не найдена — ${settings.title}`;
      return;
    }

    document.title = `${post.title} — ${settings.title}`;

    const header = el('header', 'blog-post-header');
    header.append(metadata(post, true), el('h1', '', post.title));
    if (post.description) header.append(el('p', 'blog-description', post.description));
    header.append(authorByline(post, true));

    const prose = el('div', 'blog-prose');
    for (const block of post.content) {
      if (!block) continue;
      if (block.type === 'heading' && typeof block.text === 'string') {
        prose.append(el('h2', '', block.text));
      } else if (block.type === 'paragraph' && typeof block.text === 'string') {
        prose.append(el('p', '', block.text));
      } else if (block.type === 'image') {
        const url = assetUrl(block.src);
        if (!url) continue;
        const figure = el('figure');
        figure.append(image(url, block.alt || '', () => figure.remove()));
        if (block.caption) figure.append(el('figcaption', '', block.caption));
        prose.append(figure);
      }
    }

    article.append(header, prose);
  }

  try {
    if (!settings?.title?.trim() || !config?.author?.name?.trim() ||
        !Array.isArray(config?.posts)) {
      throw new Error('Проверь settings.title, author.name и массив posts в blog-data.js.');
    }

    const ids = new Set();
    const posts = config.posts
      .filter(post => post?.draft !== true)
      .map((post, index) => {
        if (!post || typeof post.id !== 'string' || !post.id.trim() ||
            typeof post.title !== 'string' || !post.title.trim() ||
            !Array.isArray(post.tags) || !Array.isArray(post.content)) {
          throw new Error(`Запись №${index + 1}: проверь id, title, tags и content.`);
        }
        if (ids.has(post.id)) throw new Error(`Повторяется id записи: ${post.id}`);
        ids.add(post.id);

        const date = parseDate(post.date);
        if (post.date && !date) {
          throw new Error(`У записи «${post.title}» неверная дата. Формат: ГГГГ-ММ-ДД.`);
        }

        const authorName = post.author?.name ?? config.author.name;
        if (typeof authorName !== 'string' || !authorName.trim()) {
          throw new Error(`У записи «${post.title}» не указано имя автора.`);
        }

        return { post, index, time: date?.getTime() ?? -Infinity };
      })
      .sort((a, b) => b.time - a.time || a.index - b.index)
      .map(({ post }) => post);

    if (postId === null) renderList(posts);
    else renderPost(posts.find(post => post.id === postId));

    status.hidden = true;
  } catch (error) {
    root.replaceChildren();
    status.hidden = false;
    status.textContent = error.message;
    console.error('Блог Fluffy:', error);
  }
})();
