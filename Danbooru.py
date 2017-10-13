import discord
from discord.ext import commands
from urllib import parse
import aiohttp

#Danbooru search
class Danbooru():
    
    def __init__(self, bot):
        self.bot = bot
        self.usage_string = "Usage: danbooru[s] <query>"

    @commands.command(pass_context=True,no_pm=True)
    async def danboorus(self, ctx, *text):
        """Retrieves image results from Danbooru (safe images only)"""
        if len(text) > 0:
            text += ("rating:safe",)
            await self.fetch_image(ctx, randomize=True, tags=text)
        else:
            await self.bot.say(usage_string)

    @commands.command(pass_context=True,no_pm=True)
    async def danbooru(self, ctx, *text):
        """Retrieves image results from Danbooru (Warning: may include NSFW images!)"""
        if len(text) > 0:
            await self.fetch_image(ctx, randomize=True, tags=text)
        else:
            await self.bot.say(self.usage_string)

    @commands.command(pass_context=True,no_pm=True)
    async def danbooruns(self, ctx, *text):
        """Retrieves image results from Danbooru (NOT safe images only)"""
        if len(text) > 0:
            text += ("-rating:safe",)
            await self.fetch_image(ctx, randomize=True, tags=text)
        else:
            await self.bot.say(usage_string)
            
    async def fetch_image(self, ctx, randomize : bool=False, tags : list=[]):
        """
        Fetches an image from danbooru
        """
        #Initialize variables
        artist      = "unknown artist"
        artists     = ""
        artistList  = []
        embedLink   = ""
        embedTitle  = ""
        imageId     = ""
        message     = ""
        output      = None
        rating      = ""
        ratingColor = "FFFFFF"
        ratingWord  = "unknown"
        search      = "http://danbooru.donmai.us/posts.json?tags="
        tagSearch   = ""
        verbose     = True

        # Assign tags to URL
        if tags:
            tagSearch += "{} ".format(" ".join(tags))
        search += parse.quote_plus(tagSearch)

        # Randomize results
        if randomize:
            search += "&random=y"

        # Assign login information
        #if self.settings["username"] != "" and self.settings["api_key"] != "":
        #    search += "&login={}&api_key={}".format(self.settings["username"], self.settings["api_key"])

        # Inform users about image retrieval
        message = await self.bot.say("Fetching danbooru image...")

        # Fetch and display the image or an error
        try:
            async with aiohttp.get(search) as r:
                website = await r.json()
            if website != []:
                if "success" not in website:
                    for index in range(len(website)): # Goes through each result until it finds one that works
                        imageURL = None
                        # Sets the image URL
                        if "file_url" in website[index]:
                            imageURL = "https://danbooru.donmai.us{}".format(website[index].get('file_url'))
                        elif "source" in website[index]:
                            imageURL = website[index].get('source')
                            
                        if imageURL is not None:
                            if verbose:
                                # Fetches the image ID
                                imageId = website[index].get('id')

                                # Sets the embed title
                                embedTitle = "Danbooru Image #{}".format(imageId)

                                # Sets the URL to be linked
                                embedLink = "https://danbooru.donmai.us/posts/{}".format(imageId)
                                
                                # Checks for the rating and sets an appropriate color
                                rating = website[index].get('rating')
                                if rating == "s":
                                    ratingColor = "00FF00"
                                    ratingWord = "safe"
                                elif rating == "q":
                                    ratingColor = "FF9900"
                                    ratingWord = "questionable"
                                elif rating == "e":
                                    ratingColor = "FF0000"
                                    ratingWord = "explicit"

                                # Grabs the artist(s)
                                artistList = website[index].get('tag_string_artist').split()

                                # Determine if there are multiple artists
                                if len(artistList) == 1:
                                    artist = artistList[0].replace('_', ' ')
                                elif len(artistList) > 1:
                                    artists = ", ".join(artistList).replace('_', ' ')
                                    artist = ""

                                # Sets the tags to be listed
                                tagList = website[index].get('tag_string').replace(' ', ', ').replace('_', '\_')

                                # Initialize verbose embed
                                output = discord.Embed(title=embedTitle, url=embedLink, colour=discord.Colour(value=int(ratingColor, 16)))

                                # Sets the thumbnail and adds the rating and tag fields to the embed
                                output.add_field(name="Rating", value=ratingWord)
                                if artist:
                                    output.add_field(name="Artist", value=artist)
                                elif artists:
                                    output.add_field(name="Artists", value=artists)
                                output.add_field(name="Tags", value=tagList, inline=False)
                                output.set_image(url=imageURL)

                                # Edits the pending message with the results
                                return await self.bot.edit_message(message, "Image found.", embed=output)
                            else:
                                # Edits the pending message with the result
                                return await self.bot.edit_message(message, imageURL)
                                              
                    return await self.bot.edit_message(message, "Cannot find an image that can be viewed by you.")
                else:
                    # Edits the pending message with an error received by the server
                    return await self.bot.edit_message(message, "{}".format(website["message"]))
            else:
                return await self.bot.edit_message(message, "Your search terms gave no results.")
        except:
            return await self.bot.edit_message(message, "Error.")

def setup(bot):
    bot.add_cog(Danbooru(bot))
