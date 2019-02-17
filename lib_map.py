
import os
import requests
import sys
import urllib
import json
import fnmatch
import time






if len(sys.argv) < 3:
	print(f"[i] Usage:\tpython {os.path.basename(__file__)} \"tmdb_api_key\" \"path_to_movie_library\"")
	exit(0)




search_url 		= "https://api.themoviedb.org/3/search/{search}?api_key={key}&query={query}"
img_url 		= "http://api.themoviedb.org/3/{search}/{imdbid}/images?api_key={key}"
config_url 		= "https://api.themoviedb.org/3/configuration?api_key={key}"

container_dir 	= "/.Info"

key 			= sys.argv[1]
path 			= sys.argv[2]
url 			= config_url.format(key=key)
req 			= requests.get(url)
config 			= req.json()

request_pause 	= 5 # Time between api requests in seconds

base_url 		= config["images"]["secure_base_url"]
save_directory 	= "/.Info/images/"

library = {
	"movies": [],
	"series": []
}


genres = {
	28		: "Action",
	12		: "Adventure",
	16		: "Animation",
	35		: "Comedy",
	80		: "Crime",
	99		: "Documentary",
	18		: "Drama",
	10751	: "Family",
	14		: "Fantasy",
	36		: "History",
	27		: "Horror",
	10402	: "Music",
	9648	: "Mystery",
	10749	: "Romance",
	878		: "Sci-Fi",
	10770	: "TV Movie",
	53		: "Thriller",
	10752	: "War",
	37		: "Western",
	10759	: "Action & Adventure",
	10764	: "Reality",
	10763	: "News",
	10762	: "Kids",
	10765	: "Sci-Fi & Fantasy",
	10766	: "Soap",
	10767	: "Talk",
	10768	: "War & Politics"
}








def readIgnored():
	with open(".ignore", "r") as to_ignore:
		lines = []
		for line in to_ignore:
			lines.append(line.strip())

		return lines




def toFile(filename, data):
	with open(filename, "w+", encoding="utf-8") as f:
		json.dump(data, f, indent=4)



def toImageFile(filename, data):
	with open(filename, "wb") as w:
		w.write(data)



def createDirectory(dirname):
	if not os.path.exists(dirname):
		print(f"[i] Creating directory @ {dirname}")
		os.mkdir(dirname)





def createMainDirectory(dirname):
	subfolders = ["/movies", "/series"]

	if not os.path.exists(dirname):
		print(f"[i] Creating directory @ {dirname}")
		os.mkdir(dirname)

		print(f"\t[i] Creating subdirectories @ {dirname}/images")

		for subfolder in subfolders:
			print(f"\t\t[i] Creating subfolder '{subfolder}'")

			os.makedirs(os.path.join(f"{dirname}/images", f"posters{subfolder}"))
			os.makedirs(os.path.join(f"{dirname}/images", f"backdrops{subfolder}"))
		





def getMovieData():

	print("[i] Looking at movie files")

	for filename in os.listdir(path):
	
		if any(fnmatch.fnmatch(filename, pattern) for pattern in ignore):
			print(f"\t[!] Skipping {filename} in movies because of '.ignore'")
			continue

		if not os.path.isfile(os.path.join(path, filename)):	
			continue

		
		name 	= filename.split(".")[0]

		print(f"\t[/] Looking at the movie '{name}")

		query 	= urllib.parse.quote_plus(name)
		req 	= requests.get(search_url.format(search="movie", key=key, query=query))
		data 	= req.json()["results"][0]

		if len(data) == 0:
			print(f"\t\t[?] Didn't get any data back for: '{name}'")
			continue



		movie_dict = {
			"title"			: data["title"],
			"type"			: "movie",
			"genres"		: [genres[x] for x in data["genre_ids"]],
			"id"			: data["id"],
			"overview"		: data["overview"],
			"release_date"	: data["release_date"],
			"images"		: {},
			"movie_path"	: f"/{filename}",
			"file_type"		: filename.split(".")[1]
		}


		
		abs_image_paths = {
			"poster"	:base_url + "original" + data["poster_path"],
			"backdrop"	:base_url + "original" + data["backdrop_path"]
		}
		

		print(f"\t\t- Downloading images (backdrops & posters) for '{name}'\n\n")

		for (k, url) in abs_image_paths.items():
			no_space_title 	= name.replace(" ", "_")

			req 			= requests.get(url)
			filetype 		= req.headers["content-type"].split("/")[-1]

			image_name 		= f"{no_space_title}_{k}.{filetype}"
			file_path 		= f"{path}{save_directory}{k}s/movies/{image_name}"
			partial_path	= f"{save_directory}{k}s/movies/{image_name}"


			movie_dict["images"][f"{k}_path"] 			= abs_image_paths[k]
			movie_dict["images"][f"local_{k}_path"] 	= partial_path
			movie_dict["images"][f"{k}_filetype"]		= filetype

			toImageFile(file_path, req.content)
				
		
		library["movies"].append(movie_dict)

		print(f"[...] Sleeping for {request_pause} seconds\n\n")
		time.sleep(request_pause)
		break







def getSeriesData():
	season_img_url 	= "http://api.themoviedb.org/3/tv/{imdbid}/season/{nr}/images?api_key={key}"
	
	print("[i] Looking at series directories")
	
	for filename in os.listdir(path):
		
		if any(fnmatch.fnmatch(filename, pattern) for pattern in ignore):
			print(f"\t[!] Skipping {filename} in series because of '.ignore'")
			continue

			
		if os.path.isfile(os.path.join(path, filename)):
			continue

		
		query 	= urllib.parse.quote_plus(filename)
		req 	= requests.get(search_url.format(search="tv", key=key, query=query))
		data 	= req.json()["results"][0]

		if len(data) == 0:
			print(f"\t[?] Didn't get any data back for: '{filename}'")
			continue

		no_space_title 	= filename.replace(" ", "_")

		imdb_id = data["id"]
		season_index = 0
		seasons = {}

		print(f"\t\t[+] Looking at {filename}'s directory")
		for idx, s in enumerate(os.listdir(os.path.join(path, filename))):
			
			if os.path.isfile(os.path.join(path, filename, s)):
				print(f"\t\t\t- Ignoring {s} in {filename} root directory")
				
				continue
			
			else:
				season_index += 1
			

			print(f"\t\t\t[i] Looking at '{filename}' - Season {season_index}")
			

			req 		 	= requests.get(season_img_url.format(imdbid=imdb_id, nr=season_index, key=key))
			season_poster 	= req.json()["posters"][0]

			# Count episodes
			episode_count 		= 0
			current_directory 	= os.path.join(path, filename)


			for ep in os.listdir(os.path.join(current_directory, s)):

				if any(fnmatch.fnmatch(ep, pattern) for pattern in ignore):
					print(f"\t\t\t- Ignoring file {ep} in {s}")
					continue

				episode_count += 1

			print(f"\t\t\t[/] '{filename}' - Season {season_index} has a total of {episode_count} episodes")

			poster_path = base_url + "original" + season_poster["file_path"]

			seasons[season_index] = {
				"poster_path"		: poster_path,
				"ep_amount"			: episode_count,
				"season_path"		: f"/{filename}/Season_{season_index}"
			}

			print(f"\t\t\t\t- Downloading poster for '{filename}' - Season {season_index}")

			req 			= requests.get(poster_path)
			filetype 		= req.headers["content-type"].split("/")[-1]

			image_name 		= f"{no_space_title}_Season_{season_index}.{filetype}"
			file_path 		= f"{path}{save_directory}posters/series/{image_name}"
			partial_path	= f"{save_directory}posters/series/{image_name}"

			seasons[season_index]["local_poster_path"] = partial_path

			print(f"\t\t\t\t- Saving poster at {file_path}")
			toImageFile(file_path, req.content)

			season_index = 0
			


		req 		= requests.get(img_url.format(search="tv", imdbid=imdb_id, key=key))
		backdrops 	= req.json()["backdrops"][:5]


		series_dict = {
			"id"				: imdb_id,
			"type"				: "series",
			"name"				: data["name"],
			"genres"			: [genres[x] for x in data["genre_ids"]],
			"seasons_amount"	: len(seasons),
			"seasons"			: seasons,
			"backdrops"			: backdrops
		}

		print(f"\t\t[i] Downloading {len(backdrops)} backdrops for '{filename}' - All Seasons\n\n")

		for idx, backdrop in enumerate(series_dict["backdrops"]):
			file_path 		= base_url + "original" + backdrop["file_path"]
			width 			= backdrop["width"]
			height			= backdrop["height"]

			req 			= requests.get(file_path)
			filetype 		= req.headers["content-type"].split("/")[-1]

			image_name 		= f"{no_space_title}_backdrop_{idx}.{filetype}"
			file_path 		= f"{path}{save_directory}backdrops/series/{image_name}"
			partial_path 	= f"{save_directory}backdrops/series/{image_name}"

			backdrops[idx] = {
				"file_path"			: file_path,
				"local_file_path"	: partial_path,
				"width"				: width,
				"height"			: height,
				"file_type"			: filetype,
			}

			toImageFile(file_path, req.content)


		series_path = os.path.join(path, filename)

		toFile(f"{series_path}/manifest.json", series_dict)
		library["series"].append(series_dict)

		print(f"[...] Sleeping for {request_pause} seconds\n\n")
		time.sleep(request_pause)
		break











ignore = readIgnored()


createMainDirectory(f"{path}/{container_dir}")

getMovieData()
getSeriesData()

toFile(os.path.join(path, ".Info", "movies.json"), library["movies"])
toFile(os.path.join(path, ".Info", "series.json"), library["series"])
