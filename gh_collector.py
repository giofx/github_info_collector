import json
from http_module import HTTPreq
import re
import myutils

extensions_to_ignore = ["png", "jpg", "ico", "svg"]

def gh_url_for_user( username ):
    return f"https://github.com/{username}"

def gh_url_for_repository( username, repository ):
    return f"{gh_url_for_user(username)}/{repository}"

class GitHub_Collector():

    class All_Empty_ValueError( ValueError ): pass
    class API_Exception( ValueError ): pass
    class URL_Exception( ValueError ): pass
    class Username_Empty_Exception( ValueError ): pass
    class Username_Not_Valid_Exception( ValueError ): pass
    class Repository_Empty_Exception( ValueError ): pass
    class Repository_Not_Valid_Exception( ValueError ): pass

    def __init__(self, logger, username = None, repository = None, url = None):
        self.http_module = HTTPreq()
        self.logger = logger
        self.url = None

        # user typed all empty string or did not set parameters correctly
        if username in ["", None] and repository in ["", None] and  url in ["", None] :
            raise self.All_Empty_ValueError

        if url and url != "":
            
            if self.verify_github_url( url ) and self.http_module.get_with_success( url ):

                self.logger.info("%s is a valid GitHub repository URL, user and repo will be ignored even if valid", url)
                self.url = url
            else:
                self.logger.error("Url provided is not a valid GitHub repository URL, raising custom exception")
                raise self.URL_Exception

        else:
            # url is not valid, need to check user and repo
            logger.debug("URL is not defined, checking username and repository strings")

            if username and username != "":
                
                if not self.http_module.get_with_success( gh_url_for_user( username ) ):
                    self.logger.error("Username provided is not a valid GitHub username, raising custom exception")
                    raise self.Username_Not_Valid_Exception
            else:
                self.logger.error("Username field is not defined or empty string, raising custom exception")
                raise self.Username_Empty_Exception

            if repository and repository != "":

                if self.http_module.get_with_success( gh_url_for_repository( username, repository ) ):
                    # this is where you want to be
                    self.url = gh_url_for_repository( username, repository )
                    logger.info("Username and repository match a valid GitHub repository")
                else:
                    logger.error("Repository provided as arguments do not identify a valid GitHub repository for username %s", username)
                    raise self.Repository_Not_Valid_Exception
            else:
                logger.error("Repository field is not defined or empty string")
                raise self.Repository_Empty_Exception


        # we have a url for a valid project. now we need to convert it to a valid api url
        user_and_repo = self.url.split("github.com/", 1 )[1].lower()
        # convert to api schema
        self.url = f"https://api.github.com/repos/{user_and_repo}/contents/"


    def verify_github_url(self, url):
        """
            Cheks that a string follows the pattern of a GitHub repository
            At the moment only main (previously master) branch is supported
        """
        # https://regexr.com/732r3
        gh_http_schema_regex = re.compile( r'^((https?:\/\/)?(www.)?github.com(\/[\w-]+){2})$', re.IGNORECASE)
        return re.match(gh_http_schema_regex, url) is not None


    def get_files_from_url( self, url = None ):
        """
        Recursive function. Gets list of files and folders at a certain level in a GitHub repository
        """

        try:
            api_request_url = url or self.url
            api_response = self.http_module.get( api_request_url )

            if self.http_module.request_has_success( api_response["rc"] ):

                # parse data from GitHUB API. this object contains all files and folder in actual directory
                # if it's the first iteraction, this object contains the description of the root folder in the repository
                # files in subfolder must be retrieved executing the same method on the url that represent the sub folder
                objects_in_repository = json.loads( api_response["text"] )

                for object_in_repository in objects_in_repository:

                    object_type = object_in_repository["type"]

                    if object_type == "file":

                        file_name = object_in_repository["name"]
                        file_size = object_in_repository["size"]

                        self.logger.debug( "Working on file %s . Size is %s", object_in_repository["path"], str(file_size))

                        # to get extension, split name by dots
                        name_parts = file_name.split(".")
                        len_name_parts = len(name_parts)

                        # if there is only one piece, or if there is more than one piece and
                        # last piece is not in the extension to ignore
                        if len_name_parts == 1 or name_parts[-1].lower() not in extensions_to_ignore:

                            file_url = object_in_repository["download_url"]
                            
                            response_for_file_request = self.http_module.get( file_url )

                            response_status_code = response_for_file_request["rc"]

                            if self.http_module.request_has_success( response_status_code ) :
                                # if here, meands api is not expired yet and data has been downloaded
                                yield response_for_file_request["text"]
                            else:
                                self.logger.error( "%s got http status code %s while trying to retreive %s", myutils.myfunc_name(), response_status_code, file_url)
                                raise Exception( f"Exception while trying to retreive {file_url}")
                        else:
                            self.logger.debug("File analysis skipped, extension is in blacklist")

                    elif object_type == "dir":
                        yield from self.get_files_from_url( object_in_repository["url"] )

            else:
                self.logger.error( f'{myutils.myfunc_name()} got http status code {api_response["rc"]} while trying to retreive {api_request_url}')
                raise self.API_Exception

        except Exception as e:
            self.logger.error(f"{myutils.myfunc_name()} got {type(e).__name__} exception.\
                                Exception is at line {myutils.getLineLastException()}. Exception is {e}")
            raise e