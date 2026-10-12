import io
import logging
import os
import re

import discord
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from typesafe_sdk import AsyncTypeSafeClient, Choice, TypeSafeError

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

# Chart colors (dark card, so it reads the same in Discord's light and dark themes)
SURFACE = "#1a1a19"
TEXT_PRIMARY = "#f0efec"
TEXT_SECONDARY = "#c3c2b7"
TRACK = "#2c2c2a"
ANSWER_COLORS = {"yes": "#2db365", "no": "#e24337"}

SCALE = 2  # render at 2x so the image stays sharp on high-DPI screens
WIDTH = 800
PADDING = 32
BAR_HEIGHT = 20
MAX_QUESTION_LINES = 3


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf") if bold else ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf")

    for name in candidates:
        try:
            return ImageFont.truetype(name, size * SCALE)
        except OSError:
            continue

    return ImageFont.load_default(size * SCALE)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int, max_lines: int) -> list[str]:
    lines = []

    for word in text.split():
        if lines and draw.textlength(f"{lines[-1]} {word}", font=font) <= max_width:
            lines[-1] += f" {word}"
        else:
            lines.append(word)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines[-1] and draw.textlength(lines[-1] + "…", font=font) > max_width:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"

    return lines


def render_chart(question: str, probabilities: dict[str, float]) -> bytes:
    s = SCALE
    title_font = load_font(24, bold=True)
    subtitle_font = load_font(15)
    label_font = load_font(19)
    value_font = load_font(19, bold=True)

    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    inner_width = (WIDTH - 2 * PADDING) * s
    title_lines = wrap_text(measure, question, title_font, inner_width, MAX_QUESTION_LINES)

    title_line_height = 32 * s
    row_height = 70 * s
    height = (PADDING + 26 + 24) * s + len(title_lines) * title_line_height + len(probabilities) * row_height + PADDING * s

    image = Image.new("RGB", (WIDTH * s, height), SURFACE)
    draw = ImageDraw.Draw(image)

    x0 = PADDING * s
    x1 = (WIDTH - PADDING) * s
    y = PADDING * s

    for line in title_lines:
        draw.text((x0, y), line, font=title_font, fill=TEXT_PRIMARY)
        y += title_line_height

    draw.text((x0, y + 4 * s), "Model confidence", font=subtitle_font, fill=TEXT_SECONDARY)
    y += (26 + 24) * s

    for answer, probability in probabilities.items():
        # Label row: color swatch + answer name on the left, percentage on the right
        swatch = 12 * s
        draw.rounded_rectangle((x0, y + 9 * s, x0 + swatch, y + 9 * s + swatch), radius=3 * s, fill=ANSWER_COLORS[answer])
        draw.text((x0 + swatch + 10 * s, y), answer.capitalize(), font=label_font, fill=TEXT_PRIMARY)

        value_text = f"{probability:.0%}"
        draw.text((x1 - draw.textlength(value_text, font=value_font), y), value_text, font=value_font, fill=TEXT_PRIMARY)

        # Bar: full-width track with the filled share on top, rounded at the data end only
        bar_top = y + 32 * s
        bar_bottom = bar_top + BAR_HEIGHT * s
        draw.rounded_rectangle((x0, bar_top, x1, bar_bottom), radius=4 * s, fill=TRACK)

        fill_right = x0 + round((x1 - x0) * max(0.0, min(1.0, probability)))
        if fill_right > x0:
            fill_right = max(fill_right, x0 + 4 * s)
            draw.rounded_rectangle((x0, bar_top, fill_right, bar_bottom), radius=4 * s, fill=ANSWER_COLORS[answer], corners=(False, True, True, False))

        y += row_height

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


async def ask_yes_no(question: str) -> dict[str, float]:
    async with AsyncTypeSafeClient() as client:  # reads TYPESAFE_API_KEY from the environment
        response = await client.system_one(
            state="",  # required by the SDK; nothing to evaluate, just the question
            questions={"answer": Choice(instructions=question, criteria={"yes": None, "no": None})},
        )

    probabilities = response.choices["answer"].probabilities
    return {"yes": probabilities["yes"], "no": probabilities["no"]}


intents = discord.Intents.default()
intents.message_content = True
discord_bot = discord.Client(intents=intents)


def readable_question(msg: discord.Message) -> str:
    """Strip the bot's own mention and turn raw <@id>, <@&id>, <#id> and <:emoji:id> codes into readable names."""
    text = re.sub(rf"<@!?{discord_bot.user.id}>", "", msg.content)

    for user in msg.mentions:
        text = re.sub(rf"<@!?{user.id}>", f"@{user.display_name}", text)
    for role in msg.role_mentions:
        text = text.replace(f"<@&{role.id}>", f"@{role.name}")
    for channel in msg.channel_mentions:
        text = text.replace(f"<#{channel.id}>", f"#{channel.name}")

    text = re.sub(r"<a?(:\w+:)\d+>", r"\1", text)  # custom emoji -> :name:
    return " ".join(text.split())


@discord_bot.event
async def on_ready() -> None:
    logging.info(f"Logged in as {discord_bot.user}")


@discord_bot.event
async def on_message(new_msg: discord.Message) -> None:
    if new_msg.author.bot or discord_bot.user not in new_msg.mentions:
        return

    question = readable_question(new_msg)

    if not question:
        await new_msg.reply("Ask me a yes or no question, e.g. `@me Is the Earth round?`", silent=True)
        return

    logging.info(f"Question from {new_msg.author.id}: {question}")

    try:
        async with new_msg.channel.typing():
            probabilities = await ask_yes_no(question)
            chart = render_chart(question, probabilities)
    except TypeSafeError:
        logging.exception("Error while getting an answer")
        await new_msg.reply("Sorry, I couldn't get an answer for that one.", silent=True)
        return

    summary = f"Yes {probabilities['yes']:.0%} · No {probabilities['no']:.0%}"
    chart_file = discord.File(io.BytesIO(chart), filename="answer.png", description=f"{question} {summary}")

    await new_msg.reply(summary, file=chart_file, silent=True)


if __name__ == "__main__":
    if not (token := os.environ.get("DISCORD_BOT_TOKEN")):
        raise SystemExit("Set DISCORD_BOT_TOKEN in .env (Discord Developer Portal > your app > Bot > Reset Token).")

    discord_bot.run(token, log_handler=None)
