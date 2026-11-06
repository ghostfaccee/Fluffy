function detailText(error) {
  return typeof error?.detail === 'string' ? error.detail.toLowerCase() : ''
}

export function loginErrorMessage(error) {
  const text = detailText(error)
  if (error?.status === 0) return 'Нет связи с сервером. Проверь интернет и попробуй ещё раз.'
  if (error?.status === 429) return 'Слишком много попыток. Подожди минуту.'
  if (error?.status === 401 && text.includes('not activated')) {
    return 'Аккаунт ещё не активирован. Открой ссылку из письма, которое мы отправили при регистрации.'
  }
  if (error?.status === 401) return 'Неверный логин или пароль.'
  if (error?.status === 422) return 'Проверь, что логин и пароль заполнены.'
  return 'Что-то пошло не так. Попробуй позже.'
}

export function codeErrorMessage(error) {
  const text = detailText(error)
  if (error?.status === 0) return 'Нет связи с сервером. Проверь интернет и попробуй ещё раз.'
  if (error?.status === 429) return 'Слишком много попыток. Подожди минуту.'
  if (error?.status === 401 && text.includes('not found')) return 'Код истёк. Запроси новый.'
  if (error?.status === 401) return 'Неверный код.'
  if (error?.status === 404) return 'Пользователь не найден.'
  return 'Что-то пошло не так. Попробуй позже.'
}

export function registerErrorMessage(error) {
  const text = detailText(error)
  if (error?.status === 0) return 'Нет связи с сервером. Проверь интернет и попробуй ещё раз.'
  if (error?.status === 429) return 'Слишком много попыток. Подожди минуту.'
  if (error?.status === 409 || text.includes('already') || text.includes('exists') || text.includes('taken')) {
    return 'Такой логин или email уже занят.'
  }
  if (error?.status === 422) return 'Проверь, что все поля заполнены верно (логин 3–20, пароль 4–10).'
  return 'Не удалось создать аккаунт. Попробуй позже.'
}

export function profileErrorMessage(error) {
  const text = detailText(error)
  if (error?.status === 0) return 'Нет связи с сервером.'
  if (error?.status === 401) return 'Сессия истекла, войди заново.'
  if (error?.status === 404) return 'Пользователь не найден.'
  if (error?.status === 409 || text.includes('already') || text.includes('taken')) {
    return 'Такой логин или email уже занят.'
  }
  if (error?.status === 422) return 'Проверь поля: логин 3–20, email валидный.'
  return 'Не удалось сохранить изменения.'
}

export function passwordErrorMessage(error) {
  if (error?.status === 0) return 'Нет связи с сервером.'
  if (error?.status === 401) return 'Старый пароль неверный.'
  if (error?.status === 422) return 'Пароль должен быть от 3 до 10 символов.'
  return 'Не удалось сменить пароль.'
}