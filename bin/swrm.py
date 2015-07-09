#! /usr/bin/env python3

# Script to mass delete swift objects in a pseudo folder
#
# swrm.py dirkpetersen / Jul 2015 
#

import swiftclient, sys, os, math, argparse

class KeyboardInterruptError(Exception): pass

def main():
    
    if args.container:

        c=create_sw_conn()
        storageurl, authtoken = c.get_auth()
        swaccount=storageurl.split("/")[-1]

        prefix=args.prefix
        if prefix:
            if prefix.endswith('*'):
                prefix=args.prefix[:-1]
            elif not prefix.endswith('/'):
                # may be single object, try deleting
                try:
                    ret=c.delete_object(args.container,args.prefix)
                    print(ret)
                    return True
                except:
                    prefix=args.prefix+'/'
        else:
            print('no prefix / pseudo folder entered - aborting')
            return False
        
        print ("    checking swift folder /%s/%s ..." % (args.container,prefix))
        try:
            headers, objects = c.get_container(args.container,prefix=prefix,full_listing=True)
            c.close()
        except swiftclient.client.ClientException as ex:
            httperr=getattr(ex, 'http_status', None)
            if httperr == 404:
                print("    no objects found - error 404")
            else:
                print("    HTTP Error %s" % httperr)
            return False

        sbytes=0
        print("    checking size of /%s/%s ... " % (args.container,prefix))
        for obj in objects:
            sbytes+=obj['bytes']
            #print(obj['name'],obj['bytes'])
        if sbytes > 0:
            print ("        found %s files with %s bytes (%s) in /%s/%s" % (len(objects),intwithcommas(sbytes),
                  convertByteSize(sbytes),args.container,prefix))
            if not args.force:
                if yn_choice("    Do you want to delete this data in account %s ?" % swaccount):
                    easy_par(delobj,objects)
            else:
                easy_par(delobj,objects)
        else:
            print ("    ...Error: it seems swift objects at /%s/%s do not exist" % (args.container,args.prefix))

    else:
        print('no container entered - aborting')
        return False


def delobj(obj):
    print("    deleting /%s/%s ... " % (args.container,obj['name']))
    c=create_sw_conn()
    c.delete_object(args.container,obj['name'])
    c.close()

def yn_choice(message, default='n'):
    choices = 'Y/n' if default.lower() in ('y', 'yes') else 'y/N'
    choice = input("%s (%s) " % (message, choices))
    values = ('y', 'yes', '') if default == 'y' else ('y', 'yes')
    return choice.strip().lower() in values

def easy_par(f, sequence):    
    from multiprocessing import Pool
    pool = Pool(processes=args.maxproc)
    try:
        # f is given sequence. guaranteed to be in order
        cleaned=False
        result = pool.map(f, sequence)
        cleaned = [x for x in result if not x is None]
        #cleaned = asarray(cleaned)
        # not optimal but safe
    except KeyboardInterrupt:
        pool.terminate()
    except Exception as e:
        print('got exception: %r, terminating the pool' % (e,))
        pool.terminate()
    finally:
        pool.close()
        pool.join()
        return cleaned

def create_sw_conn():
    swift_auth=os.environ.get("ST_AUTH")
    if swift_auth and args.authtoken:
        return swiftclient.Connection(authurl=swift_auth,preauthtoken=args.authtoken)
    swift_user=os.environ.get("ST_USER")
    swift_key=os.environ.get("ST_KEY")
    if swift_auth and swift_user and swift_key:
        return swiftclient.Connection(authurl=swift_auth,user=swift_user,key=swift_key)

def convertByteSize(size):
   if size == 0:
        return '0 B'
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size,1024)))
   p = math.pow(1024,i)
   s = size/p
   if (s > 0):
       return '%0.3f %s' % (s,size_name[i])
   else:
       return '0 B'

def intwithcommas(x):
    result=''
    while x >= 1000:
        x,r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)


def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='swdelfolder.py',
        description='delete a pseudo folder in swift with ' + \
        'potentially many objects ' + \
        '()')
    parser.add_argument( '--container', '-c', dest='container',
        action='store',
        help='a container in the swift object store',
        default='' )
    parser.add_argument( '--prefix', '-p', dest='prefix',
        action='store',
        help='a swift object prefix',
        default=None)
    parser.add_argument( '--force', '-f', dest='force',
        action='store_true',
        help='force delete without prompt',
        default=False)
    parser.add_argument( '--maxproc', '-m', dest='maxproc',
        action='store',
        type=int,
        help='maximum number of processes to run',
        default=32 )
    parser.add_argument( '--authtoken', '-a', dest='authtoken',
        action='store',
        help='a swift authentication token',
        default=None)    
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()
    sys.exit(main())
