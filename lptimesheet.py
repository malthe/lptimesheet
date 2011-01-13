#!/usr/bin/python2.7

import argparse
import getpass
import urllib2
import json
import sys
import iso8601
import datetime
import time

parser = argparse.ArgumentParser(
    description='LiquidPlanner Timesheet Extraction and Formatting Tool'
    )

parser.add_argument('email', type=str, metavar='email',
                    help='Used for authentication.')
parser.add_argument('workspace', type=str, metavar='workspace',
                    help='Workspace name.')
parser.add_argument(
    'start_date',
    type=str,
    metavar='start-date',
    help='The start date (YYYY/MM/DD).'
    )
parser.add_argument(
    'end_date',
    type=str,
    metavar='end-date',
    help='The start date (YYYY/MM/DD).'
    )
parser.add_argument('-t', '--total', required=False,
                    action='store_const', const=True,
                    help="Output only total registered work hours.")
parser.add_argument(
    '--format', type=str, metavar='type', default="json", required=False,
    help="Output format; available formats are: 'json' and 'html'.",
    )

args = parser.parse_args()

# get password
password = getpass.getpass("Enter password for %s:" % args.email)

# set up HTTPS fetch function
password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
top_level_url = "https://app.liquidplanner.com/api/"
password_mgr.add_password(None, top_level_url, args.email, password)
handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)

def fatal(msg):
    parser.print_usage()
    print "\nerror:\n\n" + msg
    sys.exit(-1)

def fetch(relative_url):
    fp = opener.open(top_level_url + relative_url)
    return json.load(fp)

# find workspace
names = []
for workspace in fetch("workspaces"):
    if args.workspace.lower() in workspace['name'].lower():
        break
    names.append(workspace['name'])
else:
    fatal("Workspace '%s' not found in list:\n\n%s." % (
        args.workspace,
        "\n".join("%3.d - %s" % (i + 1, name) for (i, name) in \
                  enumerate(names))
        ))

# get member id
print >> sys.stderr, "===> Loading members ..."
for member in fetch("workspaces/%d/members" % workspace['id']):
    if member['email'] == args.email:
        break
else:
    fatal("Unable to find member id for email: %s." % args.email)

# get projects
projects_by_id = {
    None: {
    'name': None,
        }
    }

print >> sys.stderr, "===> Loading projects ..."
for project in fetch("workspaces/%d/projects" % workspace['id']):
    projects_by_id[project['id']] = project

# get activities
task_by_item_id = {}
print >> sys.stderr, "===> Loading activities ..."
for task in fetch("workspaces/%d/tasks" % workspace['id']):
    item_id = task['id']
    if item_id is not None:
        task_by_item_id[item_id] = task

# get timesheet
print >> sys.stderr, "===> Loading timesheet ..."
timesheet = fetch("workspaces/%d/timesheet_entries" % workspace['id'])

date_format = "%Y/%m/%d"

projects = {}
total = 0

start_time = time.strptime(args.start_date, date_format)[0:6]
end_time = time.strptime(args.end_date, date_format)[0:6]

if not args.total:
    def register_entry(entry):
        item_id = entry['item_id']
        t = task_by_item_id[item_id]
        name = t['name']
        project_id = t['project_id']

        project = projects.setdefault(project_id, {
            'tasks': {},
            'name': projects_by_id[project_id]['name']
            })

        task = project['tasks'].setdefault(item_id, {
            'entries': [],
            'name': name,
            'work': 0.0,
            })

        task['entries'].append(entry)
        task['work'] += entry['work']

        return True
else:
    def register_entry(entry):
        pass

print >> sys.stderr, "===> Compiling entries ..."

for entry in timesheet:
    if entry['member_id'] != member['id']:
        continue

    updated_at = iso8601.parse_date(entry['updated_at'])
    start_date = datetime.datetime(*start_time, tzinfo=updated_at.tzinfo)
    end_date = datetime.datetime(*end_time, tzinfo=updated_at.tzinfo)

    if updated_at >= start_date and updated_at <= end_date:
        # only include items that have been submitted for review
        if entry['state'] != 'submitted':
            item_id = entry['item_id']
            t = task_by_item_id[item_id]
            name = t['name']
            print >> sys.stderr, \
                  "!    Ignoring task with state '%s': %s (%d hours)." % (
                entry['state'], name, entry['work'])
            continue

        register_entry(entry)
        total += entry['work']

if args.total:
    print total
    sys.exit()

output = {
    'total': total,
    'projects': projects,
    }

if args.format == 'json':
    print json.dumps(output)
    sys.exit()

if args.format == 'html':
    from chameleon.zpt.template import PageTemplateFile
    print >> sys.stderr, "===> Rendering template ..."
    template = PageTemplateFile("template.pt")
    result = template(data=output, **args.__dict__)
    print result.encode('utf-8')
    sys.exit()
