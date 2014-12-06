# -*- coding: utf-8 -*-

import os
import re

from .. import utils
from . import init


def command(config, repo, commit, upstream, commit_hash):
    """Updates Puppetfile and base branch accordingly
    """
    puppetfile = utils.PuppetFile(repo)
    puppetfile.load()

    # update Puppetfile
    branch = utils.get_current_branch(repo)

    # Some puppet modules could have an underscore instead of a dash in their
    # name. !
    basename = re.split('puppet-|puppet_',
                        os.path.basename(upstream))[-1].split('.', 1)[0]
    _locals = locals()
    utils.shout(
        'Adding new module module {basename}'.format(**_locals),
        verbose=True,
        level='info'
    )
    puppetfile[basename] = {'git': upstream, 'commit': commit_hash}
    puppetfile.save()
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git stash'.format(**_locals)
    )

    # sync base branch
    init.create_module_branch(repo, branch, basename, puppetfile[basename])
    init.import_module_branch(repo, branch, basename)
    rc, stdout, stderr = utils.execute(
        'cd {repo} && '
        'git checkout {branch} && '
        'git stash apply && '
        'git stash drop'.format(**_locals),
        can_fail=False
    )
    if rc:
        utils.shout(
            'Failed to unstash Puppetfile changes:'
                '\n{stdout}'.format(**_locals),
            verbose=True,
            level='warning'
        )

    if commit:
        utils.shout(
            'Generating commit',
            verbose=config.verbose,
            level='info'
        )
        status = (
            '{basename}\\n - initial commit: {commit_hash}'
            '\\n\\n'.format(**_locals)
        )
        msg = utils.COMMIT_MSG.format(status)
        rc, stdout, stderr = utils.execute(
            'cd {repo} && '
            'git add {basename} --ignore-errors && '
            'git add Puppetfile && '
            'git commit -m $\'{msg}\''.format(**locals())
        )
