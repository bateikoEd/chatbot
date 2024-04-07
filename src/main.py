from aiohttp import web

app = web.Application()


async def handle(request):
    return web.json_response({'is_limit_reached': False})

app.router.add_route('*', '/{tail:.*}', handle)

web.run_app(app, host="0.0.0.0", port=9090)

# http://localhost:9090/is_limit_reached?model=capybara&user_id=172.18.0.1