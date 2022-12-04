# python modules
import sys
import logging
import argparse
from enum import Enum

# custom modules
import myutils
from data_ingestor import Data
from gh_collector import GitHub_Collector


class Exit_Code(Enum):
    SUCCESS = 0
    GENERIC_ERROR_PARAMETERS = 1
    ALL_EMPTY_PARAMS = 2
    URL_EXCEPTION = 3
    USERNAME_EMPTY_EXCEPTION = 4
    USERNAME_NOT_VALID_EXCEPTION = 5
    REPOSITORY_EMPTY_EXCEPTION = 6
    REPOSITORY_NOT_VALID_EXCEPTION = 7
    DOWNLOAD_EXCEPTION = 8
    API_EXCEPTION = 9
    UNKNOWN_EXCEPTION = 255


def argv_to_conf():
    """
        converts cli arguments to a dictionary with all user inputs correctly classified
    """

    cli_parser = argparse.ArgumentParser( description = "GitHub Info Collector, looks for relevant data in GitHub repositories" )
     
    cli_parser.add_argument("-l", help = "GitHub Link. Example: https://github.com/python/cpython . Has priority on -u and -r")
    cli_parser.add_argument("-u", help = "GitHub Username")
    cli_parser.add_argument("-r", help = "GitHub Repository")
    
    collect_group = cli_parser.add_argument_group()
    collect_group.add_argument("--addresses",   help = "collect addresses from repository",     action="store_true")
    collect_group.add_argument("--emails",      help = "collect emails from repository",        action="store_true")
    collect_group.add_argument("--telephones",  help = "collect telephones from repository",    action="store_true")
    collect_group.add_argument("--tokens",      help = "collect tokens from repository",        action="store_true")
    collect_group.add_argument("--urls",        help = "collect urls from repository",          action="store_true")

    output_group = cli_parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", help = "set output text format to JSON", action = "store_true")
    output_group.add_argument("--json-file", help = "if followed by a valid file name, text will be written to that file in JSON format, otherwise printed to stdout")
    output_group.add_argument("--yaml", help = "set output text format to YAML", action = "store_true")
    output_group.add_argument("--yaml-file", help = "if followed by a valid file name, text will be written to that file in YAML format, otherwise printed to stdout")
    
    args = cli_parser.parse_args()

    conf = {
        "collect":
        {
            "addresses" : args.addresses,
            "emails" : args.emails,
            "telephones" : args.telephones,
            "tokens" : args.tokens,
            "urls" : args.urls
        },
        "github":
        {
            "user" : args.u ,
            "repo" : args.r ,
            "url" : args.l 
        },
        "output":
        {
            "json" : args.json,
            "json_file" : args.json_file,
            "yaml" : args.yaml,
            "yaml_file" : args.yaml_file
        }
    }

    return conf


def main():

    logging.basicConfig(
        filename = "./logs/" + sys.argv[0] + ".log" ,
        filemode = "a",
        format = "%(asctime)s %(levelname)s %(message)s",
        level = logging.DEBUG
    )

    logger = logging.getLogger(__name__)

    try:
        conf = argv_to_conf()
        logger.debug( "conf after user input %s", str(conf) )

    except Exception as e:
        logger.error( "Got %s exception at line %s while trying to parse arguments. \
            Exception is %s", type(e).__name__ ,str(myutils.getLineLastException()), str(e) )
        sys.exit( Exit_Code.GENERIC_ERROR_PARAMETERS.value )


    logger.debug("All parameter have been read, can proceed with connection to github and data collection")

    try:
        # initializing github info stealer
        collector = GitHub_Collector(logger, conf["github"]["user"], conf["github"]["repo"], conf["github"]["url"])
    except ValueError as e:

        message = str(e)
        exit_code = Exit_Code.UNKNOWN_EXCEPTION.value

        if type(e) == GitHub_Collector.All_Empty_ValueError:
            message = "All inputs needed to identify a valid GitHub repository are not properly filled. Specify a Username and Repository with -u and -r or a link with -l . Application will close"
            exit_code = Exit_Code.ALL_EMPTY_PARAMS.value
        elif type(e) == GitHub_Collector.URL_Exception:
            message = "URL provided does not match a valid GitHub repository. Application will close"
            exit_code = Exit_Code.ALL_EMPTY_PARAMS.value
        elif type(e) == GitHub_Collector.Username_Not_Valid_Exception:
            message = "Username provided does not match a valid GitHub user. Application will close"
            exit_code = Exit_Code.USERNAME_NOT_VALID_EXCEPTION.value
        elif type(e) == GitHub_Collector.Username_Empty_Exception:
            message = "Username field is empty. Application will close"
            exit_code = Exit_Code.USERNAME_EMPTY_EXCEPTION.value
        elif type(e) == GitHub_Collector.Repository_Empty_Exception:
            message = "Repository field is empty. Application will close"
            exit_code = Exit_Code.REPOSITORY_EMPTY_EXCEPTION.value
        elif type(e) == GitHub_Collector.Repository_Not_Valid_Exception:
            message = "Repository provided does not match a valid GitHub repository for user. Application will close"
            exit_code = Exit_Code.REPOSITORY_NOT_VALID_EXCEPTION.value

        logger.error( message )
        print( message , file=sys.stderr)
        sys.exit(exit_code)

    except Exception as e:
        message = f"Got {type(e).__name__} Exception while trying to initialize GitHub Collector. Application will close"
        logger.error( message )
        print( message , file=sys.stderr)
        sys.exit(Exit_Code.UNKNOWN_EXCEPTION.value)



    logger.debug("GitHub data collector initialized with no exceptions. Going to initialize data ingestor and then read files")

    # Data is a custom class that owns all collected data and has algorithms to ingest data from files
    data = Data(conf["collect"]["addresses"] , conf["collect"]["emails"], conf["collect"]["telephones"], conf["collect"]["tokens"], conf["collect"]["urls"])

    try:

        for file_as_text in collector.get_files_from_url():

            data.ingest( file_as_text )

    except GitHub_Collector.API_Exception:
        message = "Got Exception from GitHub API. Execution is now stopped. Partial data will not be printed"
        logger.error(message)
        print(message, file=sys.stderr)
        sys.exit( Exit_Code.API_EXCEPTION.value )
    except Exception as e:
        message = f"Got {type(e).__name__} Exception while trying to retrieve data. Execution is now stopped. Partial data will not be printed"
        logger.error(message)
        print(message, file=sys.stderr)
        sys.exit( Exit_Code.DOWNLOAD_EXCEPTION.value )


    logger.debug("Interaction with GitHub got no exception. Going to print the result")

    if conf["output"]["yaml"]:

        logger.debug("Printing data as text in yaml format")
        output = data.export_as_YAML()
        print(output)

    elif conf["output"]["yaml_file"] and conf["output"]["yaml_file"] != "":
        
        logger.debug("A file name is defined, going to try to write text to %s", conf["output"]["yaml_file"])
        output = data.export_as_YAML()

        try:
            with open( conf["output"]["yaml_file"] , "w", encoding="utf8") as file:
                file.write(output)
            logger.info("Data successfully written to %s", conf["output"]["yaml_file"])
        except Exception as e:
            logger.error("%s exception while trying to write text to file %s, printing text to stdout", {type(e).__name__}, {conf["output"]["yaml_file"]})
            print(output)

    elif conf["output"]["json"]:

        logger.debug("Printing data as text in json format")
        output = data.export_as_JSON()
        print(output)

    elif conf["output"]["json_file"] and conf["output"]["json_file"] != "":

        logger.debug('A file name is defined, going to try to write text to %s', conf["output"]["json_file"])
        output = data.export_as_JSON()
        
        try:
            with open( conf["output"]["json_file"] , "w", encoding="utf8") as file:
                file.write(output)
            logger.info("Data successfully written to %s", conf["output"]["json_file"])
        except Exception as e:
            logger.error("%s exception while trying to write text to file %s, printing text to stdout", type(e).__name__ , conf["output"]["json_file"])
            print(output)

    else:
        # default case
        print( data )


if __name__ == "__main__":
    main()