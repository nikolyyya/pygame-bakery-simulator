import pygame

WIDTH, HEIGHT, FPS = 1000, 650, 60
RADIUS = 22
SPEED = 260.0
START_MONEY = 420
DONE_SHOW_TIME = 2.0          

NO_ORDER = "NO_ORDER"
WAITING = "WAITING"
READY = "READY"
DONE = "DONE"

MSG_DEFAULT = "Сделайте заказ возле прилавка"

CLIENT_COLORS = [
    (70, 130, 220),
    (60, 180, 110),
    (220, 90, 80),
    (230, 175, 60),
]

MENU_RECT = pygame.Rect(410, 10, 580, 600)

TEXT_COLOR = (40, 40, 40)
MENU_TEXT_COLOR = (100, 10, 5)


def create_products():
    return [
        {"name": "Хлеб", "price": 70, "stock": 3, "cook_time": 0},
        {"name": "Булочка", "price": 90, "stock": 4, "cook_time": 0},
        {"name": "Сэндвич", "price": 180, "stock": 2, "cook_time": 5.0},
        {"name": "Кофе", "price": 140, "stock": 5, "cook_time": 3.0},
    ]


def create_zones():
    return {
        "entrance": pygame.Rect(0, 250, 90, 120),
        "counter": pygame.Rect(400, 40, 240, 120),
        "cash": pygame.Rect(800, 40, 120, 120),
        "pickup_area": pygame.Rect(800, 400, 200, 200),

        "order_zone": pygame.Rect(400, 170, 240, 120),
        "pickup_zone": pygame.Rect(650, 400, 145, 200),
    }


def create_state():
    return {
        "running": True,
        "position": pygame.Vector2(120, 300),
        "color_index": 0,
        "menu_open": False,
        "money": START_MONEY,
        "order_state": NO_ORDER,
        "current_product": None,  
        "cook_total": 0.0,         
        "cook_left": 0.0,        
        "done_left": 0.0,          
        "message": MSG_DEFAULT,
    }


# ---------------------------------------------------------------
# Вспомогательные функции (ничего не рисуют и не меняют состояние)
# ---------------------------------------------------------------
def client_rect(position):
    rect = pygame.Rect(0, 0, RADIUS * 2, RADIUS * 2)
    rect.center = (round(position.x), round(position.y))
    return rect


def hits_obstacle(position, zones):
    rect = client_rect(position)
    return rect.colliderect(zones["counter"]) or rect.colliderect(zones["cash"])


def get_available_action(state, zones):
    """Какое действие по E доступно прямо сейчас: 'order', 'pickup' или None."""
    if state["menu_open"]:
        return None

    rect = client_rect(state["position"])

    if rect.colliderect(zones["order_zone"]) and state["order_state"] == NO_ORDER:
        return "order"
    if rect.colliderect(zones["pickup_zone"]) and state["order_state"] == READY:
        return "pickup"
    return None

def make_order(state, product):
    if product["stock"] <= 0:
        state["message"] = "Товар закончился"
    elif state["money"] < product["price"]:
        state["message"] = "Недостаточно денег"
    else:
        state["menu_open"] = False
        state["money"] -= product["price"]
        product["stock"] -= 1
        state["current_product"] = product
        state["message"] = "Заказ принят"

        if product["cook_time"] > 0:
            state["order_state"] = WAITING
            state["cook_total"] = product["cook_time"]
            state["cook_left"] = product["cook_time"]
        else:
            state["order_state"] = READY


def interact(state, zones):
    """Нажата клавиша E."""
    if state["menu_open"]:
        return

    rect = client_rect(state["position"])
    order_state = state["order_state"]
    action = get_available_action(state, zones)

    if action == "order":
        state["menu_open"] = True
        state["message"] = "Просмотр меню"

    elif action == "pickup":
        state["order_state"] = DONE
        state["done_left"] = DONE_SHOW_TIME
        state["message"] = "Заказ получен"

    elif rect.colliderect(zones["order_zone"]):
        if order_state == WAITING:
            state["message"] = "Ваш заказ ещё готовится"
        elif order_state == READY:
            state["message"] = "Заберите заказ в зоне выдачи"

    elif rect.colliderect(zones["pickup_zone"]):
        if order_state == WAITING:
            state["message"] = "Ожидайте приготовления заказа"
        elif order_state == NO_ORDER:
            state["message"] = "Вы ещё не сделали заказ"


def handle_events(state, products, zones):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state["running"] = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                state["running"] = False

            elif event.key == pygame.K_SPACE:
                state["color_index"] = (state["color_index"] + 1) % len(CLIENT_COLORS)

            elif event.key == pygame.K_e:
                interact(state, zones)

            elif event.key == pygame.K_r:
                if state["menu_open"]:
                    state["menu_open"] = False
                    state["message"] = MSG_DEFAULT

            elif state["menu_open"] and pygame.K_1 <= event.key < pygame.K_1 + len(products):
                make_order(state, products[event.key - pygame.K_1])


def handle_movement(state, zones, dt):
    keys = pygame.key.get_pressed()

    direction = pygame.Vector2(0, 0)
    if keys[pygame.K_w]:
        direction.y -= 1
    if keys[pygame.K_s]:
        direction.y += 1
    if keys[pygame.K_a]:
        direction.x -= 1
    if keys[pygame.K_d]:
        direction.x += 1

    if state["menu_open"]:
        direction = pygame.Vector2(0, 0)
    elif direction.length_squared() > 0:
        direction = direction.normalize()

    step = direction * SPEED * dt
    position = state["position"]

    new_x = max(RADIUS, min(WIDTH - RADIUS, position.x + step.x))
    if not hits_obstacle(pygame.Vector2(new_x, position.y), zones):
        position.x = new_x

    new_y = max(RADIUS, min(HEIGHT - RADIUS, position.y + step.y))
    if not hits_obstacle(pygame.Vector2(position.x, new_y), zones):
        position.y = new_y

def update_order(state, dt):
    if state["order_state"] == WAITING:
        state["cook_left"] -= dt

        if state["cook_left"] <= 0:
            state["cook_left"] = 0
            state["order_state"] = READY
            state["message"] = "Заказ готов! Заберите его в зоне выдачи"

    elif state["order_state"] == DONE:
        state["done_left"] -= dt

        if state["done_left"] <= 0:
            state["order_state"] = NO_ORDER
            state["current_product"] = None
            state["message"] = MSG_DEFAULT


def center_label(text, color, rect, font, screen):
    label = font.render(text, True, color)
    screen.blit(label, label.get_rect(center=rect.center))


def draw_scene(screen, state, zones, fonts):
    font = fonts["big"]
    screen.fill((245, 245, 245))

    pygame.draw.rect(screen, (100, 110, 125), zones["entrance"], border_radius=10)
    pygame.draw.rect(screen, (10, 50, 200), zones["cash"], border_radius=10)
    pygame.draw.rect(screen, (100, 180, 60), zones["counter"], border_radius=10)

    pickup_color = (230, 150, 20) if state["order_state"] == READY else (100, 10, 80)
    pygame.draw.rect(screen, pickup_color, zones["pickup_area"], border_radius=10)

    rect = client_rect(state["position"])
    for key in ("order_zone", "pickup_zone"):
        active = rect.colliderect(zones[key])
        pygame.draw.rect(
            screen,
            (60, 170, 90) if active else (175, 175, 175),
            zones[key],
            width=3,
            border_radius=10,
        )

    pygame.draw.circle(
        screen,
        CLIENT_COLORS[state["color_index"]],
        (round(state["position"].x), round(state["position"].y)),
        RADIUS,
    )

    white = (255, 255, 255)
    center_label("Прилавок", white, zones["counter"], font, screen)
    center_label("Касса", white, zones["cash"], font, screen)
    center_label("Зона выдачи", white, zones["pickup_area"], font, screen)
    center_label("Вход", white, zones["entrance"], font, screen)


def draw_menu(screen, products, fonts):
    font = fonts["big"]
    x, y = MENU_RECT.x, MENU_RECT.y

    pygame.draw.rect(screen, (250, 250, 250), MENU_RECT, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), MENU_RECT, width=5, border_radius=10)

    title_rect = pygame.Rect(x, y + 10, MENU_RECT.width, 30)
    center_label("Меню", MENU_TEXT_COLOR, title_rect, font, screen)

    hint = font.render(f"Чтобы сделать заказ, нажмите 1-{len(products)}", True, MENU_TEXT_COLOR)
    screen.blit(hint, (x + 20, y + 55))

    for i, prod in enumerate(products):
        line_y = y + 110 + i * 70

        if prod["cook_time"] > 0:
            cook_text = f"готовится {prod['cook_time']:.0f} с"
        else:
            cook_text = "готов сразу"

        line1 = font.render(f"{i + 1}. {prod['name']}: {prod['price']} руб.", True, MENU_TEXT_COLOR)
        line2 = font.render(f"В наличии: {prod['stock']} шт., {cook_text}", True, MENU_TEXT_COLOR)
        screen.blit(line1, (x + 20, line_y))
        screen.blit(line2, (x + 40, line_y + 25))

    close_hint = font.render("R — закрыть меню", True, TEXT_COLOR)
    screen.blit(close_hint, (x + 20, MENU_RECT.bottom - 45))


def draw_cooking_indicator(screen, state, fonts):
    font = fonts["big"]
    bar_x, bar_y, bar_w, bar_h = 40, 580, 500, 32

    if state["order_state"] == WAITING:
        name = state["current_product"]["name"]
        title = font.render(
            f"Готовится: {name}. Осталось: {state['cook_left']:.1f} с", True, TEXT_COLOR
        )
        screen.blit(title, (bar_x, bar_y - 30))

        progress = 1.0 - state["cook_left"] / state["cook_total"]
        progress = max(0.0, min(1.0, progress))

        pygame.draw.rect(screen, (215, 215, 215), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
        pygame.draw.rect(
            screen, (70, 160, 100), (bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=6
        )

    elif state["order_state"] == READY:
        title = font.render("Заказ готов! Заберите его в зоне выдачи", True, (40, 120, 65))
        screen.blit(title, (bar_x, bar_y))


def draw_ui(screen, state, zones, fonts, clock):
    font = fonts["big"]
    small = fonts["small"]

    msg = font.render(state["message"], True, TEXT_COLOR)
    screen.blit(msg, (15, 15))

    product = state["current_product"]
    cooking = f"{state['cook_left']:.1f} с" if state["order_state"] == WAITING else "—"
    action = get_available_action(state, zones)
    action_text = {"order": "E — сделать заказ", "pickup": "E — забрать заказ"}.get(action, "—")

    lines = [
        f"Деньги: {state['money']} руб.",
        f"Заказ: {product['name'] if product else '—'}",
        f"Состояние: {state['order_state']}",
        f"Приготовление: {cooking}",
        f"Действие: {action_text}",
    ]
    for i, line in enumerate(lines):
        label = small.render(line, True, TEXT_COLOR)
        screen.blit(label, (15, 50 + i * 24))

    if action == "order":
        zone = zones["order_zone"]
        prompt_rect = pygame.Rect(zone.x, zone.bottom + 5, zone.width, 30)
        center_label("E — сделать заказ", (40, 120, 65), prompt_rect, font, screen)
    elif action == "pickup":
        zone = zones["pickup_zone"]
        prompt_rect = pygame.Rect(zone.x - 30, zone.y - 35, zone.width + 60, 30)
        center_label("E — забрать заказ", (40, 120, 65), prompt_rect, font, screen)

    draw_cooking_indicator(screen, state, fonts)

    info = small.render(
        f"FPS: {clock.get_fps():.0f} | WASD — движение | E — действие | "
        "R — закрыть меню | SPACE — цвет | ESC — выход",
        True,
        (70, 70, 70),
    )
    screen.blit(info, (20, 630))


def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MyBakery")
    clock = pygame.time.Clock()

    fonts = {
        "big": pygame.font.Font(None, 30),
        "small": pygame.font.Font(None, 24),
    }

    products = create_products()
    zones = create_zones()
    state = create_state()

    try:
        while state["running"]:
            dt = clock.tick(FPS) / 1000.0

            handle_events(state, products, zones)
            handle_movement(state, zones, dt)
            update_order(state, dt)

            draw_scene(screen, state, zones, fonts)
            if state["menu_open"]:
                draw_menu(screen, products, fonts)
            draw_ui(screen, state, zones, fonts, clock)

            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()