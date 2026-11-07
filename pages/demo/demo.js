(() => {
  const root = document.documentElement;
  const toast = document.getElementById('toast');
  let toastTimer;
  const showToast = (message) => {
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2400);
  };
  const pages = {
    home: 'Главная',
    profile: 'Мой профиль',
    chats: 'Сообщения',
    groups: 'Группы',
    settings: 'Настройки'
  };
  function openPage(name) {
    if (!pages[name]) return;
    document.querySelectorAll('.page').forEach(page => page.classList.toggle('active', page.id === 'page-' + name));
    document.querySelectorAll('[data-page]').forEach(button => button.classList.toggle('active', button.dataset.page === name));
    document.getElementById('crumb').textContent = pages[name];
    document.querySelector('.main').scrollIntoView({behavior:'smooth',block:'start'});
  }
  document.querySelectorAll('[data-page]').forEach(button => button.addEventListener('click', () => openPage(button.dataset.page)));
  document.getElementById('themeToggle').addEventListener('click', () => {
    const next = root.dataset.theme === 'light' ? 'dark' : 'light';
    root.dataset.theme = next;
    localStorage.setItem('fluffy-demo-theme', next);
    document.getElementById('themeToggle').textContent = next === 'light' ? '☾' : '☼';
  });
  const savedTheme = localStorage.getItem('fluffy-demo-theme');
  if (savedTheme === 'light') {
    root.dataset.theme = 'light';
    document.getElementById('themeToggle').textContent = '☾';
  }
  document.querySelectorAll('[data-theme]').forEach(button => button.addEventListener('click', () => {
    root.dataset.theme = button.dataset.theme;
    localStorage.setItem('fluffy-demo-theme', button.dataset.theme);
    document.querySelectorAll('[data-theme]').forEach(item => item.classList.toggle('selected', item === button));
    document.getElementById('themeToggle').textContent = button.dataset.theme === 'light' ? '☾' : '☼';
  }));
  const chats = {
    maria: {name:'Мария Волкова',letter:'М',avatar:'avatar-pink',status:'была недавно',messages:[['in','Привет! Как твои дела?','12:38'],['out','Привет! Всё отлично, работаю над Fluffy ✨','12:40'],['in','Выглядит очень уютно!','12:42']]},
    nikita: {name:'Никита Орлов',letter:'Н',avatar:'avatar-blue',status:'в сети',messages:[['in','Привет! Есть планы на выходные?','Вчера'],['out','Думаю поработать над интерфейсом.','Вчера'],['in','Увидимся на выходных?','Вчера']]},
    team: {name:'Fluffy Community',letter:'F',avatar:'avatar-violet',status:'3 участника недавно были в сети',messages:[['in','Мария: Я посмотрела обновления!','Пн'],['out','Класс, спасибо за обратную связь.','Пн'],['in','Алина: Отличная идея!','Пн']]}
  };
  function selectChat(id) {
    const chat = chats[id];
    if (!chat) return;
    document.querySelectorAll('.chat-person').forEach(item => item.classList.toggle('selected', item.dataset.chat === id));
    const avatar = document.getElementById('activeChatAvatar');
    avatar.className = 'avatar ' + chat.avatar;
    avatar.textContent = chat.letter;
    document.getElementById('activeChatName').textContent = chat.name;
    document.getElementById('activeChatStatus').textContent = chat.status;
    document.getElementById('messages').innerHTML = '<div class="day-divider">История демо-переписки</div>' + chat.messages.map(([kind,text,time]) => '<div class="message ' + (kind === 'out' ? 'outgoing' : 'incoming') + '">' + escapeHtml(text) + '<time>' + time + '</time></div>').join('');
  }
  document.querySelectorAll('[data-chat]').forEach(button => button.addEventListener('click', () => {
    openPage('chats');
    selectChat(button.dataset.chat);
  }));
  function escapeHtml(value) {
    return value.replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  }
  document.getElementById('messageForm').addEventListener('submit', event => {
    event.preventDefault();
    const input = document.getElementById('messageInput');
    const value = input.value.trim();
    if (!value) return;
    const message = document.createElement('div');
    message.className = 'message outgoing';
    message.textContent = value;
    const time = document.createElement('time');
    time.textContent = 'сейчас';
    message.appendChild(time);
    document.getElementById('messages').appendChild(message);
    input.value = '';
    document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
    showToast('Сообщение добавлено в демо-переписку');
  });
  const groups = {
    community:['Fluffy Community','Обсуждаем развитие проекта, делимся идеями и помогаем друг другу.','✳'],
    design:['Design corner','Интерфейсы, визуальные эксперименты и хороший дизайн.','⌘'],
    talks:['Разговоры обо всём','Небольшие разговоры о больших и маленьких вещах.','⌁']
  };
  document.querySelectorAll('.group-open').forEach(button => button.addEventListener('click', () => {
    const group = groups[button.dataset.group];
    document.getElementById('groupDetail').classList.remove('hidden');
    document.getElementById('detailName').textContent = group[0];
    document.getElementById('detailDescription').textContent = group[1];
    document.getElementById('detailArt').textContent = group[2];
    document.getElementById('groupDetail').scrollIntoView({behavior:'smooth',block:'nearest'});
  }));
  document.getElementById('backGroups').addEventListener('click', () => document.getElementById('groupDetail').classList.add('hidden'));
  document.getElementById('createGroup').addEventListener('click', () => showToast('Создание групп доступно только в полной версии Fluffy'));
  document.getElementById('editProfile').addEventListener('click', () => showToast('Редактирование профиля доступно только в полной версии Fluffy'));
  document.getElementById('searchInput').addEventListener('keydown', event => {
    if (event.key !== 'Enter') return;
    const query = event.currentTarget.value.trim().replace(/^@/,'');
    if (!query) return;
    if (query.toLowerCase() === 'alex_demo' || query.toLowerCase() === 'alex') openPage('profile');
    else showToast('В демо доступен только профиль @alex_demo');
    event.currentTarget.value = '';
  });
})();