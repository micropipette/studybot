from discord_components import Button, ButtonStyle, InteractionType
import asyncio
import discord
from discord.ext import commands
from utils.utilities import textToEmoji
from collections import defaultdict

REACTIONS = "abcdefghijklmnopqrstuvwxyz"


async def send_result(mcq: bool,
                      ctx: commands.Context,
                      res,
                      options: list,
                      correct_index: int) -> None:
    '''
    Sends the result of a quiz given the user's response
    '''
    if mcq:
        # Determine whether MCQ answer is correct or not

        ind = ord(res.component.label.lower()) - 97

        ctx.current_mcq += 1  # Add 1 to total MCQ
        if ind == correct_index:
            ctx.current_score += 1  # Add 1 to current score
            e = discord.Embed(
                colour=discord.Color.green(), title="Correct",
                description=textToEmoji(REACTIONS[correct_index]) + " " + options[correct_index])
        else:
            e = discord.Embed(
                colour=discord.Color.red(), title="Incorrect",
                description=textToEmoji(REACTIONS[correct_index]) + " " + options[correct_index])

        e.set_footer(text=f"You Answered: {res.component.label}\nCurrent Score: {ctx.current_score}/{ctx.current_mcq} = {round(ctx.current_score/ctx.current_mcq*100)}%")

    else:
        # Show flashcard answer
        e = discord.Embed(
            colour=discord.Color.green())

        answers = "\n".join(options)

        e.set_author(name="Answer", icon_url="https://media.discordapp.net/attachments/724671574459940974/856634979001434142/unknown.png")

        if options and len(answers) < 256:
            e.title = answers
        elif options:
            e.description = answers
        else:
            e.title = "(No Answer Found)"

    # NEW: Makes answers only visible to the author
    await res.message.edit(components=[])
    await res.respond(type=InteractionType.ChannelMessageWithSource, is_ephemeral=True, embeds=[e])


async def send_result_mp(mcq: bool,
                      ctx: commands.Context,
                      res,
                      options: list,
                      correct_index: int) -> None:
    '''
    Sends the result of a quiz given the user's response
    '''
    if mcq:
        # Determine whether MCQ answer is correct or not

        ind = ord(res.component.label.lower()) - 97

        ctx.current_mcq[res.author.id] += 1  # Add 1 to total MCQ
        if ind == correct_index:
            ctx.current_score[res.author.id] += 1  # Add 1 to current score
            e = discord.Embed(
                colour=discord.Color.green(), title="Correct",
                description=textToEmoji(REACTIONS[correct_index]) + " " + options[correct_index])
        else:
            e = discord.Embed(
                colour=discord.Color.red(), title="Incorrect",
                description=textToEmoji(REACTIONS[correct_index]) + " " + options[correct_index])

        e.set_footer(text=f"You Answered: {res.component.label}\nCurrent Score: {ctx.current_score[res.author.id]}/{ctx.current_mcq[res.author.id]} = {round(ctx.current_score[res.author.id]/ctx.current_mcq[res.author.id]*100)}%")

    else:
        # Show flashcard answer
        e = discord.Embed(
            colour=discord.Color.green())

        answers = "\n".join(options)

        e.set_author(name="Answer", icon_url="https://media.discordapp.net/attachments/724671574459940974/856634979001434142/unknown.png")

        if options and len(answers) < 256:
            e.title = answers
        elif options:
            e.description = answers
        else:
            e.title = "(No Answer Found)"

    # NEW: Makes answers only visible to the author
    await res.respond(type=InteractionType.ChannelMessageWithSource, is_ephemeral=True, embeds=[e])


async def listen_quiz(ctx: commands.Context, questions: list):
    ctx.current_score = 0
    ctx.current_mcq = 0

    while questions:
        # Verify list is not empty

        current_question = questions.pop(0)
        prompt = current_question[0]

        if not prompt:
            continue
            # Move to next question since this one is empty

        image_url = current_question[1]
        mcq = False

        e = discord.Embed(color=discord.Color.blue())

        desc_text = ""

        if len(prompt) < 252:
            e.title = f"**{prompt}**"
        else:
            desc_text = f"**{prompt}**\n"

        e.set_footer(
                text=f"{ctx.author.display_name}, press 🛑 to stop the quiz.")

        options = [
            op.strip("\n") for op in current_question[
                2:-1] if op]  # Take only non blank entries

        if image_url:
            e.set_image(url=image_url)

        if current_question[-1]:
            # Multiple choice
            mcq = True

            if len(options) > 24:
                await ctx.send(f"Error, Question `{prompt}` has {len(options)} options, which exceeds the allowed maximum of 24.")
                continue

            correct_index: int = ord(current_question[-1][0].lower()) - 97

            if correct_index > len(current_question) - 1:
                await ctx.send(f"Error, Question `{prompt}` has an invalid 'Correct Answer' label. Please make sure the correct answer is labelled as {{A, B, C, D, etc.}}")
                continue

            for i in range(len(options)):
                desc_text += f"{textToEmoji(REACTIONS[i])}: {options[i]}\n"

            e.description = desc_text  # Add the MCQ options to the description
            # Description now has question text (maybe) + mcq questions

            e.set_author(
                name="Select the correct answer",
                icon_url=ctx.author.avatar_url)
        else:
            correct_index: int = 0
            # Give it a default value so as to not raise an error
            e.set_author(
                name="Press ✅ to see the answer",
                icon_url=ctx.author.avatar_url)

        components = [[]]

        def add_component(component):
            if len(components[-1]) < 5:
                components[-1].append(component)
            else:
                components.append([component])

        if mcq:
            for i in range(len(options)):
                add_component(Button(label=REACTIONS[i].upper()))
        else:
            add_component(Button(label="✅", style=ButtonStyle.green))

        add_component(Button(label="🛑", style=ButtonStyle.red))

        msg = await ctx.channel.send(embed=e, components=components)  # Message that bot sends

        def check(res):
            return res.author.id == ctx.author.id and res.message.id == msg.id

        try:
            res = await ctx.bot.wait_for("button_click", timeout=120, check=check)

            if res.component.label == "🛑":
                finalscore = f"Final Score: {ctx.current_score}/{ctx.current_mcq} = {round(ctx.current_score/ctx.current_mcq*100)}%" if ctx.current_mcq else None
                await res.respond(type=InteractionType.UpdateMessage, components=[])

                end_embed = discord.Embed(title="Quiz Terminated. Enter a new link to start again!",
                              description = ("\n"+finalscore) if finalscore else "", colour=discord.Colour.red())
                end_embed.set_author(icon_url=ctx.author.avatar_url, name=f"Quiz for {ctx.author.display_name}")
                await ctx.channel.send(embed=end_embed)
                return

            await send_result(
                mcq, ctx, res, options, correct_index)

        except asyncio.TimeoutError:
            await msg.edit(
                content="**Quiz timed out after 120 seconds of inactivity.**")
            return

    finalscore = f"Final Score: {ctx.current_score}/{ctx.current_mcq} = {round(ctx.current_score/ctx.current_mcq*100)}%" \
                 if ctx.current_mcq else None

    end_embed = discord.Embed(title="Question deck has been exhausted. Enter a new link to start again!",
                              description = ("\n"+finalscore) if finalscore else "", colour=discord.Colour.dark_grey())

    end_embed.set_author(icon_url=ctx.author.avatar_url, name=f"Quiz for {ctx.author.display_name}")
    await ctx.channel.send(embed=end_embed)
    return


async def listen_quiz_mp(ctx: commands.Context, questions: list):
    ctx.current_score = defaultdict(int)
    ctx.current_mcq = defaultdict(int)

    while questions:
        # Verify list is not empty

        current_question = questions.pop(0)
        prompt = current_question[0]

        if not prompt:
            continue
            # Move to next question since this one is empty

        image_url = current_question[1]
        mcq = False

        e = discord.Embed(color=discord.Color.blue())

        desc_text = ""

        if len(prompt) < 252:
            e.title = f"**{prompt}**"
        else:
            desc_text = f"**{prompt}**\n"

        e.set_footer(
                text=f"{ctx.author.display_name}, press 🛑 to stop the quiz.")

        options = [
            op.strip("\n") for op in current_question[
                2:-1] if op]  # Take only non blank entries

        if image_url:
            e.set_image(url=image_url)

        if current_question[-1]:
            # Multiple choice
            mcq = True

            if len(options) > 24:
                await ctx.send(f"Error, Question `{prompt}` has {len(options)} options, which exceeds the allowed maximum of 24.")
                continue

            correct_index: int = ord(current_question[-1][0].lower()) - 97

            for i in range(len(options)):
                desc_text += f"{textToEmoji(REACTIONS[i])}: {options[i]}\n"

            e.description = desc_text  # Add the MCQ options to the description
            # Description now has question text (maybe) + mcq questions

            e.set_author(
                name="Select the correct answer",
                icon_url=ctx.author.avatar_url)
        else:
            correct_index: int = 0
            # Give it a default value so as to not raise an error
            e.set_author(
                name="Press ✅ to see the answer",
                icon_url=ctx.author.avatar_url)

        components = [[]]

        def add_component(component):
            if len(components[-1]) < 5:
                components[-1].append(component)
            else:
                components.append([component])

        if mcq:
            for i in range(len(options)):
                add_component(Button(label=REACTIONS[i].upper()))
        else:
            add_component(Button(label="✅", style=ButtonStyle.green))

        add_component(Button(label="🛑", style=ButtonStyle.red))

        msg = await ctx.channel.send(embed=e, components=components)  # Message that bot sends

        def check(res):
            return res.message.id == msg.id

        async def listen_button():
            while 1:
                # Perpetual control loop
                res = await ctx.bot.wait_for("button_click", check=check)

                if res.component.label == "🛑":
                    await res.respond(type=InteractionType.UpdateMessage, components=[])

                    standings = discord.Embed(title="Final Standings")
                    standings.set_author(name="Quiz Terminated. Enter a new link to start again!")
                    standings.description = "\n".join([f"<@{id}>: {ctx.current_score[id]}/{ctx.current_mcq[id]} = {round(ctx.current_score[id]/ctx.current_mcq[id]*100)}%" for id in ctx.current_mcq])

                    await ctx.channel.send(embed=standings)
                    return

                await send_result_mp(
                    mcq, ctx, res, options, correct_index)

        t = asyncio.create_task(listen_button())
        await asyncio.sleep(10)  # Delay

        if t.done():
            # if the stop button was pressed
            return

        t.cancel() # cancel task of waiting for buttons

        # Terminate this question

        standings = discord.Embed(title="Standings")
        standings.description = "\n".join([f"<@{id}>: {ctx.current_score[id]}/{ctx.current_mcq[id]} = {round(ctx.current_score[id]/ctx.current_mcq[id]*100)}%" for id in ctx.current_mcq])
        await msg.edit(components=[])
        await ctx.send(embed=standings)


    standings = discord.Embed(title="Final Standings")
    standings.set_author(name="Question deck has been exhausted. Enter a new link to start again!")
    standings.description = "\n".join([f"<@{id}>: {ctx.current_score[id]}/{ctx.current_mcq[id]} = {round(ctx.current_score[id]/ctx.current_mcq[id]*100)}%" for id in ctx.current_mcq])

    await ctx.channel.send(embed=standings)
    return
