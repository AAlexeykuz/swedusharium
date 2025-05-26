import asyncio

import g4f
import g4f.Provider
import g4f.providers

providers = [
    # g4f.Provider.DDG,
    # g4f.Provider.Blackbox,
    # g4f.Provider.ChatGptEs,
    # g4f.Provider.TypeGPT,
    g4f.Provider.PollinationsAI,
    # g4f.Provider.Liaobots,
    # g4f.Provider.OpenaiChat,
]
# gpt_4o_mini = Model(
#     name          = 'gpt-4o-mini',
#     base_provider = 'OpenAI',
#     best_provider = IterListProvider([DDG, Blackbox, ChatGptEs, TypeGPT, PollinationsAI, OIVSCode, Liaobots, Jmuz, OpenaiChat])
# )

best_providers = {
    "4o-mini": (
        g4f.Provider.ChatGptEs,
        g4f.Provider.PollinationsAI,
        g4f.Provider.Blackbox,
    )
}


async def run_provider(provider: g4f.Provider.BaseProvider):
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_4o_mini,
            messages=[{"role": "user", "content": "В чём смысл жизни?"}],
        )
        print(f"{provider.__name__}:", response)
    except Exception as e:
        print(f"{provider.__name__}:", e)


async def run_all():
    calls = [run_provider(provider) for provider in providers]
    await asyncio.gather(*calls)


asyncio.run(run_all())
