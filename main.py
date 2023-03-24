import discord
import requests
from bs4 import BeautifulSoup
import re
import asyncio


client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_message(message):
    if message.content.startswith('!tv'):
        query = message.content[4:]
        if " " in query:
          query = query.replace(" ", "%20")
        else:
          query = query.replace(" ", "+")


        # Fetch data from IMDb API
        imdb_api_url = "https://imdb-api.com/en/API/SearchSeries/k_onigfri1/" + query
        imdb_api_response = requests.get(imdb_api_url)
        imdb_api_data = imdb_api_response.json()
        
        if not imdb_api_data['results']:
            await message.channel.send("No results found.")
            return
        
        # Get first result from IMDb API search
        imdb_id = imdb_api_data['results'][0]['id']
        imdb_title = imdb_api_data['results'][0]['title']
        imdb_link = f"https://www.imdb.com/title/{imdb_id}"
        imdb_year = imdb_api_data['results'][0]['description']
        imdb_poster = imdb_api_data['results'][0]['image']
        imdb_year_final = imdb_year.split()[0][:imdb_year.index(" ")]
        if re.search(r'\D$', imdb_year_final):
            imdb_year_final += "Ongoing"
            
        # Fetch Rotten Tomatoes data from IMDb API
        rt_api_url = f"https://imdb-api.com/en/API/Ratings/k_onigfri1/{imdb_id}"
        rt_api_response = requests.get(rt_api_url)
        rt_api_data = rt_api_response.json()
        
        rt_critics_score = rt_api_data['rottenTomatoes']
        if any(char.isdigit() for char in str(rt_critics_score)):
            rt_critics_score = str(rt_critics_score) + "%" # add percentage sign if value exists and contains numeric digits
        else:
            rt_critics_score = 'N/A'
        
        # Make a GET request to the website
        url = 'https://www.commonsensemedia.org/search/' + query
        response = requests.get(url)
        print(response)
        
        # Parse the HTML content using Beautiful Soup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get the link of the first search result
        result_link = soup.find('h3', {'class': 'review-title'}).find('a')['href']

        complete_link = "https://www.commonsensemedia.org" + result_link
        response2 = requests.get(complete_link)
        soup2 = BeautifulSoup(response2.content, 'html.parser')
        parents_say_age = soup2.find('div', {'class': 'col-6'}).find('span', {'class': 'rating__age'}).text.strip()
        parents_say_age = parents_say_age.replace('a', 'A')
        try:
            kids_say_age = soup2.find_all('div', {'class': 'rating rating--user rating--xlg'})[1].find('span', {'class': 'rating__age'}).text.strip()
            kids_say_age = kids_say_age.replace('a', 'A')
        except IndexError:
            kids_say_age = 'N/A'
        
        # Find the first review-rating div and get the age rating
        review_rating = soup.find('div', class_='review-rating')
        age_rating = review_rating.find('div', class_='rating rating--inline').span.text.strip()
        age_rating_final = age_rating[age_rating.rfind(' ')+1:] if ' ' in age_rating else age_rating
        csm_age = 'Age ' + age_rating_final
        csm_age = csm_age.replace('a', 'A')

        csm_result = "Overall: " + csm_age + "\n" + "Parents Say: " + parents_say_age + "\n" + "Kids Say: " + kids_say_age

    
        # Create the embed
        embed = discord.Embed(title=imdb_title, url=imdb_link, color=0x00ff00)
        embed.set_thumbnail(url=imdb_poster)
        embed.add_field(name="Release Year", value=imdb_year_final, inline=True)
        embed.add_field(name="Rotten Tomatoes Score", value=rt_critics_score, inline=True)
        embed.add_field(name="CSM Age Rating", value=csm_result, inline=True)
        
        await message.channel.send(embed=embed)
      
        def check(msg):
            return msg.author == message.author and msg.channel == message.channel
        

        categoryembedmessage = 'React with ✅ if you want to see the categories.'
        trailerembedmessage = 'React with 📽 if you want to see the trailer'
        category_embed = discord.Embed(title="Options")
        category_embed.add_field(name="Categories", value=categoryembedmessage, inline=True)
        category_embed.add_field(name="Trailer", value=trailerembedmessage, inline=True)
        category_embed.set_footer(text="This message will be deleted in 20 seconds if you don't react.")
    
        category_message = await message.channel.send(embed=category_embed)
        await category_message.add_reaction('✅')
        await category_message.add_reaction('📽')
            
        try:
            reaction_ctx = await client.wait_for("reaction_add", check=lambda reaction, user: user == message.author and str(reaction.emoji) in ['✅', '📽'], timeout=20)
        
            if str(reaction_ctx[0].emoji) == '✅':
                # User wants to know the categories
                buttonpage = "https://www.commonsensemedia.org" + result_link
                buttonresponse = requests.get(buttonpage)
                buttonsoup = BeautifulSoup(buttonresponse.content, 'html.parser')
                category_buttons = buttonsoup.find_all('button', {'class': 'rating rating--sm'})
                categories = []
                for category in category_buttons:
                    category_name = category.find('span', {'class': 'rating__label'}).text.strip()
                    rating = category.find_all('i', {'class': 'icon-circle-solid active'})
                    rating_out_of_5 = len(rating)
                    categories.append(f"{category_name}: {rating_out_of_5}/5")
                for category in soup2.find_all('span', class_='csm-green-age'):
                    categories.append(category.text.strip())

                # Extract the language rating
                for rating in categories:
                    if rating.startswith('Language'):
                        languagescore = int(rating.split(': ')[1][0])
                        finallanguagescore = str(languagescore) + '/5'
                    elif rating.startswith('Violence & Scariness'):
                        violencescore = int(rating.split(': ')[1][0])
                        finalviolencescore = str(violencescore) + '/5'
                    elif rating.startswith('Sex, Romance & Nudity'):
                        romancescore = int(rating.split(': ')[1][0])
                        finalromancescore = str(romancescore) + '/5'
                    elif rating.startswith('Drinking, Drugs & Smoking'):
                        drinkingscore = int(rating.split(': ')[1][0])
                        finaldrinkingscore = str(drinkingscore) + '/5'
                        break
                embed = discord.Embed(title='Categories', url=imdb_link, color=0x00ff00)
                embed.set_thumbnail(url=imdb_poster)
                embed.add_field(name="Violence & Scariness", value=finalviolencescore, inline=True)
                embed.add_field(name="Sex, Romance and Nudity", value=finalromancescore, inline=True)
                embed.add_field(name="Language", value=finallanguagescore, inline=True)
                embed.add_field(name="Drinking, Drugs and Smoking", value=finaldrinkingscore, inline=True)

                await message.channel.send(embed=embed)
                await category_message.delete()
            # Find the trailer link and send it.
            elif str(reaction_ctx[0].emoji) == '📽':
                url = 'https://www.googleapis.com/youtube/v3/search'
                params = {
                    'key': 'GOOGLEAPIKEY', # Replace this with a real Google Api Token, follow this tutorial: https://is.gd/62Onyo.
                    'channelId': 'UCi8e0iOVk1fEOogdfu4YgfA',
                    'part': 'id',
                    'order': 'relevance',
                    'type': 'video',
                    'q': query
                }
                
                # Send the API request
                response = requests.get(url, params=params)
                
                # Parse the response and extract the video links
                json_data = response.json()
                video_link = None
                for item in json_data['items']:
                    video_id = item['id']['videoId']
                    video_link = f'https://www.youtube.com/watch?v={video_id}'
                    break
                trailermessage = f"**Trailer Video**\n{video_link}"
                await message.channel.send(trailermessage)
                await category_message.delete()
              
        except asyncio.TimeoutError:
            print("Took too long.")
            await category_message.delete()


client.run('TOKEN') # Replace with your actual Discord bot token.
