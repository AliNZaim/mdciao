##############################################################################
#    This file is part of mdciao.
#    
#    Copyright 2025 Charité Universitätsmedizin Berlin and the Authors
#
#    Authors: Guillermo Pérez-Hernandez
#    Contributors:
#
#    mdciao is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    mdciao is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with mdciao.  If not, see <https://www.gnu.org/licenses/>.
##############################################################################

from os import path as _path, getcwd as _getcwd, chdir as _chdir, link as _link, mkdir as _mkdir
from shutil import copy as _shcopy
from glob import glob as _glob
from mdciao import __path__ as mdc_path
from subprocess import run as _run
from zipfile import ZipFile as _ZF
from mdciao.filenames import FileNames as _FN
import mdtraj as _md

filenames = _FN()
mdc_path = _path.split(mdc_path[0])[0]

long2short = {"--residues" : "-r",
              "--n_smooth_hw" : "-ns",
              "--table_ext" : "-tx",
              "--GPCR_UniProt" : "--GPCR",
              "--CGN_UniProt"   : "--CGN"
              }

long2long = {key:key for key in long2short.keys()}

from requests import get as _rget
from tqdm.auto import tqdm as _tqdma
import contextlib as _contextlib
from mdciao.cli import residue_neighborhoods as _residue_neighborhoods, interface as _interface
from mdciao.nomenclature import LabelerGPCR as _LabelerGPCR, LabelerCGN as _LabelerCGN, LabelerKLIFS as _LabelerKLIFS, AlignerConsensus as _AlignerConsensus
from tempfile import TemporaryDirectory as _TDir, TemporaryFile as _TF
from mdciao.fragments import get_fragments as _get_fragments
import io as _io
@_contextlib.contextmanager
def remember_cwd():
    curdir = _getcwd()
    try:
        yield
    finally:
        _chdir(curdir)

class ExamplesCLTs(object):
    def __init__(self, test=False, short=False):
        r"""
        API interface to show or call the mdc_* scripts from the command line directly

        For instance, self.run("mdc_interface") will run an mdc_interface.py example

        Parameters
        ----------
        test : bool, default is False
            If True, internally all references to input filenames
            are converted from full paths to basenames, because
            it is assumed that the test method is calling the
            self.run() method form a temporary directory
            where links to these filenames have been
            created already. Additionally, the flag
            "-ni" for non-interactive runs is added to the methods
            that would otherwise prompt the user for some confirmations
        short : bool, default is False
            Whether to use the short or the long versions
            of the flags
        """
        self.xtc = filenames.traj_xtc
        self.pdb = filenames.top_pdb
        self.GPCRlabs_file = filenames.adrb2_human_xlsx
        self.KLIFSlabs_file = filenames.KLIFS_P31751_xlsx
        self.CGN_file = filenames.gnas2_human_xlsx
        self.sitefile = filenames.tip_json
        self.pdb_3SN6 = filenames.rcsb_3SN6_pdb
        self.KLIFS_pdb = filenames.rcsb_3E8D_pdb

        self.test = test
        cwd = _getcwd()
        for fn in ["xtc", "pdb", "GPCRlabs_file", "CGN_file", "sitefile", "pdb_3SN6"]:
            attr_val = getattr(self, fn)
            if self.test:
                setattr(self, fn, _path.basename(attr_val))
            else:
                setattr(self, fn, _path.relpath(attr_val,cwd))

        if short:
            self.opt_dict=long2short
        else:
            self.opt_dict = long2long
    @property
    def mdc_neighborhoods(self):
        return ["mdc_neighborhoods.py",
                "%s %s" % (self.pdb, self.xtc),
                self.opt_dict["--residues"] + " L394",
                self.opt_dict["--n_smooth_hw"] + " 1",
                self.opt_dict["--table_ext"] + " xlsx",
                self.opt_dict["--GPCR_UniProt"] + " %s" % self.GPCRlabs_file,
                self.opt_dict["--CGN_UniProt"] + " %s" % self.CGN_file,
                ]
    @property
    def mdc_sites(self):
        return ["mdc_sites.py ",
                "%s %s" % (self.pdb, self.xtc),
                " --site_files %s" % self.sitefile,
                " --GPCR_UniProt %s" % self.GPCRlabs_file,
                " --CGN_UniProt %s" % self.CGN_file
                ]

    @property
    def mdc_interface(self):
        return ["mdc_interface.py ",
                "%s %s" % (self.pdb, self.xtc),
                " --interface_selection_1 0-2",
                " --interface_selection_2 3",
                " --ctc_control 20",
                " --GPCR_UniProt %s" % self.GPCRlabs_file,
                " --CGN_UniProt %s" % self.CGN_file,
                ]
    @property
    def mdc_GPCR_overview(self):
        return ["mdc_GPCR_overview.py",
                "%s" % self.GPCRlabs_file,
                "-t %s" % self.pdb]

    @property
    def mdc_KLIFS_overview(self):
        return ["mdc_KLIFS_overview.py",
                "%s" % self.KLIFSlabs_file,
                "-t %s" % self.KLIFS_pdb]

    @property
    def mdc_CGN_overview(self):
        # This is the only one that needs network access
        return ["mdc_CGN_overview.py",
                "%s" % 'gnas2_human',
                "-t %s" % self.pdb,
                ]

    @property
    def mdc_compare(self):
        return ["mdc_neighborhoods.py",
                "%s %s" % (self.pdb, self.xtc),
                self.opt_dict["--residues"] + " L394",
                self.opt_dict["--n_smooth_hw"] + " 1",
                self.opt_dict["--table_ext"] + " xlsx",
                "--ctc_cutoff_Ang 3",
                "\n\n",
                "mdc_neighborhoods.py",
                "%s %s" % (self.pdb, self.xtc),
                self.opt_dict["--residues"] + " L394",
                self.opt_dict["--n_smooth_hw"] + " 1",
                self.opt_dict["--table_ext"] + " xlsx",
                "--ctc_cutoff_Ang 4",
                "\n\n"
                "mdc_compare.py",
                "neighborhood.LEU394@frag0@3.0_Ang.xlsx",
                "neighborhood.LEU394@frag0@4.0_Ang.xlsx"
                ]
        pass

    @property
    def mdc_fragments(self):
        return ["mdc_fragments.py ",
                "%s" % (self.pdb)
                ]
        pass

    @property
    def mdc_pdb(self):
        return ["mdc_pdb.py 3SN6"]

    @property
    def mdc_residues(self):
        return ["mdc_residues.py ",
                "P0G,380-394,3.5* "
                "%s"% (self.pdb),
                " --GPCR_UniProt %s" % self.GPCRlabs_file,
                "-ni"]

    @property
    def mdc_notebooks(self):
        return ["mdc_notebooks.py "]

    @property
    def clts(self):
        return [attr for attr in dir(self) if attr.startswith("mdc")]

    def _assert_clt_exists(self, clt):
        assert clt in self.clts, "Input method %s is not in existing methods %s" % (clt, self.clts)

    def _join_args(self,clt):
        oneline = self.__getattribute__(clt)
        # Only add the -ni argument where it's needed
        if self.test and all([istr not in clt for istr in ["_overview", "mdc_fragments", "mdc_pdb", "mdc_compare", "mdc_notebooks"]]):
            oneline += ["-ni"]
        return " ".join(oneline)

    def show(self, clt):
        self._assert_clt_exists(clt)
        print("%s example call:" % clt)
        print("%s--------------"%("".join(["-" for _ in clt]))) # really?
        oneline = self._join_args(clt)
        print(oneline.replace(" -", " \n-"))
        print("\n\nYou can re-run 'mdc_examples %s.py' with the '-x' option to execute the command directly\n"
              "or you can paste the line below into your terminal, add/edit options and then execute:\n"%clt)
        print(oneline)

    def run(self, clt,show=True):
        if show:
            self.show(clt)
        oneline = self._join_args(clt)
        CP = []
        for line in oneline.split("\n\n"):
            CP.append(_run(line.split(), capture_output=self.test))
        if self.test:
            return CP

@_contextlib.contextmanager
def _linkorcopy2TDir(suffix, filelist):
    r"""
    Context manager to wraps around :obj:`tempfile.TemporaryDirectory` and link (or copy) the files from `filelist` there

    If an "Invalid cross-device link" is found, it copies instead of links the file

    Parameters
    ----------
    suffix : string
        passed do :obj:`tempfile.TemporaryDirectory`
    filelist : list
        The list of files to be copied to the TemporaryDirectory

    Returns
    -------
    None
    """
    with _TDir(suffix=suffix) as t:
        for fn in filelist:
            try:
                _link(fn, _path.join(t, _path.basename(fn)))
            except OSError:
                _shcopy(fn, _path.join(t, _path.basename(fn)))
        yield t

def ContactGroupL394(**kwargs):
    r"""
    Create an example :obj:`mdciao.contacts.ContactGroup` quickly.

    Wraps around :obj:`mdciao.cli.residue_neighborhoods` and asks
    for the LEU394 neighborhood.

    The input data is one very short (56 frames) version
    of the MD trajectory shipped with mdciao, kindly provided by
    Dr. H. Batebi. See the online examples for more info.

    Parameters
    ----------
    kwargs : optional keyword arguments
        For :obj:`mdciao.cli.residue_neighborhoods`

    Returns
    -------
    CG : a :obj:`~mdciao.contacts.ContactGroup`

    """
    with _linkorcopy2TDir("_mdciao_example_CG",
                          [filenames.traj_xtc,
                           filenames.top_pdb,
                           filenames.adrb2_human_xlsx,
                           filenames.gnas2_human_xlsx]) as t:
        with remember_cwd():
            _chdir(t)
            b = _io.StringIO()
            try:
                with _contextlib.redirect_stdout(b):
                    example_kwargs = {"topology": _path.basename(filenames.top_pdb),
                                      "n_smooth_hw": 1,
                                      "figures": False,
                                      "GPCR_UniProt": _path.basename(filenames.adrb2_human_xlsx),
                                      "CGN_UniProt": _path.basename(filenames.gnas2_human_xlsx),
                                      "no_disk":True,
                                      "accept_guess": True}
                    for key, val in kwargs.items():
                        example_kwargs[key]=val
                    return _residue_neighborhoods("L394",
                                                  _path.basename(filenames.traj_xtc),
                                                  **example_kwargs,
                                                  )[353]

            except Exception as e:
                print(b.getvalue())
                b.close()
                raise e

def notebooks(folder ="mdciao_notebooks"):
    r"""
    Copy the example Jupyter notebooks distributed with mdciao to this folder.

    The method never overwrites an existing folder, but
    keeps either asking or producing new folder names.

    Parameters
    ----------
    folder : str

    Returns
    -------
    folder : str
        The folder to which the notebooks were copied
        Can be identical to the input or one generated
        by :obj:`_recursive_prompt`.

    """

    pwd = _getcwd()

    nbs = sorted(_glob(_path.join(filenames.notebooks_path,"*.ipynb")))

    dest = _recursive_prompt(_path.join(pwd, folder), folder, verbose=True)
    print("Copying file(s):"
          "\n -%s"%"\n -".join(nbs))
    _mkdir(dest)
    print("Here:")
    for ff in nbs:
        _shcopy(ff,dest)
        print(" %s"%_path.join(dest,_path.basename(ff)))

    return dest

def _recursive_prompt(input_path, pattern, count=1, verbose=False, is_file=False, skip_on_existing=False):
    r"""
    Ensure input_path doesn't exist and keep generating/prompting for alternative filenames/dirnames

    Poorman's attempt at actually a good recursive function, but does its job.
    A maximum recursion depth of 50 is hard-coded

    Parameters
    ----------
    input_path : str
        Example, "path/to/mdicao_example.zip"
    pattern : str
        The part of input_path used to generate new filenames,
        example "mdciao_example"
    count : int, default is 0
        Where in the recursion we are
    verbose : bool, default is False
    is_file : bool, default is False
        Name-generating is different for folders than
        from files:
        * mdciao_notebook -> mdciao_notebook_00
        * mdciao_example.zip -> mdciao_example_00.zip
    skip_on_existing : bool, default is False
        If the `input_path` is found, instead of
        prompting for a new path, simply skip this
        method and return the `input_path` without
        doing anything.
    Returns
    -------
    nox_path : str
        By default, `new_path` is a newly created,
        previously non-existent path. If the
        `input_path` existed, the default is to create
        a `new_path`, unless `skip_on_existing` was set
        to True, in which case nothing happens and the
        existing `input_path` is returned without
        doing anything.

    """

    max_recurr = 50
    cwd = _getcwd()
    ext = _path.splitext(input_path)[1]
    while _path.exists(input_path):
        if verbose:
            print("%s exists" % input_path)
            if skip_on_existing:
                break
        input_path = _path.join(cwd, pattern) + "_%02u" % count
        if is_file:
            input_path += ext
        count += 1
        if count > max_recurr:
            raise RecursionError("Over %u files/folders exist with the '%s' pattern, aborting" % (max_recurr, pattern))

    if count>1:
        print(input_path, "will be created")
        print("Hit Enter to accept or provide another path from %s%s:\r"%(cwd,_path.sep))
        answer = input()
    else:
        answer = ""
    if len(answer)==0:
        return input_path
    else:
        input_path = _path.join(cwd, answer)
        print("OK, your suggestion is",input_path)
    if _path.exists(input_path):
        print("%s already exists. Next suggestion:" % input_path)
        return _recursive_prompt(input_path, pattern, count=count, verbose=verbose, is_file=is_file)
    else:
        return _path.join(cwd,answer)


def fetch_example_data(alias_or_url="b2ar@Gs",
                       unzip=True,
                       skip_on_existing=False):
    r""" Download example data as zipfile and unzip it to the working directory.

    The available datasets are (see below for full info)
     * 'b2ar@Gs'
     * 'EGFR'
     * 'cov19'
     * 'ghrelin@ghsr'
     * 'mor@muor'
     * 'y1_apo'

    This data is used in the notebooks:
     * 01.Tutorial.ipynb (b2ar@Gs)
     * 02.Missing_Contacts.ipynb (b2ar@Gs)
     * 03.Comparing_CGs_Bars.ipyn (cov19)
     * 04.Comparing_CGs_Flares.ipynb (cov19)
     * 07.EGFR Kinase Inhibitors.ipynb (EGFR)
     * 08.Manuscript.ipynb (b2ar@Gs)
     * 09.Consensus_labels.ipynb (ghrelin@ghsr,b2ar@Gs,mor@muor,y1_apo)

    which can all be run locally issuing,
    from the CLI:

    >>>  mdc_notebooks.py

    or from the API:

    >>> mdciao.examples.notebooks()

    Note
    ----
    By default, a zipfile is downloaded and then extracted
    to a directory with its own name. If these files already
    exist, the user will be prompted for new filenames
    s.t. no files are ever overwritten when extracting. Use
    `unzip` to change filenames a priory and `skip_on_existing`
    to simply skip either the downloading or the unzipping.

    Parameters
    ----------
    alias_or_url : str
        The url or the alias to download example data.
        Currently, these are the available aliases and their urls
         * b2ar@Gs : https://proteinformatics.uni-leipzig.de/mdciao/mdciao_example.zip
          Beta 2 adrenergic receptor in complex with Gs-protein. Provided
          kindly by Dr. H. Batebi (1 traj, ca. 10 MB, 280 frames, dt = 10 ps)

         * EGFR : http://proteinformatics.uni-leipzig.de/mdciao/example_kinases.zip
          Epidermal Growth Factor Receptor (EGFR) in complex with
          four inhibitors. The inhibitors and their PDB IDs are
          P31@3POZ, W321@3W32, EUX1@6LUB and  7VH1@7VRE.
          The data has been generated using `TeachOpenCADD <https://projects.volkamerlab.org/teachopencadd/index.html>`_ .
          (4 trajs, ca 10 MB each, ca 500 frames each, dt = 1ns)

         * cov19 : https://proteinformatics.uni-leipzig.de/mdciao/example_cov19.zip
          SARS-CoV-2 spike protein receptor binding domain (RBD) bound
          to human angiotensin converting enzyme-related carboypeptidase (ACE2).
          The files already contain processed trajectory data, in the form
          of mdciao.contacts.ContactGroup-objects stored as npy files.
          Original data generated at the Chodera Lab by Ivy Zhang,
          made available via `molSSI <https://covid.molssi.org//simulations/#foldinghome-simulations-of-the-sars-cov-2-spike-rbd-bound-to-human-ace2>`_.
          (1 npy file with interfaces for 4 setups and one sample trajectory file, ca 42 MB)

         * ghrelin@ghsr : https://proteinformatics.uni-leipzig.de/mdciao/ghrelin_receptor.zip
          Growth hormone secretagogue receptor type 1, ghrelin receptor for short, bound
          to ghrelin. Provided kindly by Dr. A. Vogel (1 traj, ca. 10 MB, 411 frames, dt = 100ns).
          For the associated publication see here:

           * Analysis of the Dynamics of the Human Growth Hormone Secretagogue Receptor Reveals Insights into the Energy Landscape of the Molecule
             A. A. Smith, E. M. Pacull, S. Stecher, P. W. Hildebrand, A. Vogel, D. Huster
             Angew. Chem. Int. Ed. 2023, 62, e202302003 `<https://doi.org/10.1002/anie.202302003>`_

         * y1_apo : https://proteinformatics.uni-leipzig.de/mdciao/y1_apo.zip
          Neuropeptide Y receptor type 1, Y1 receptor for short, in apo form.
          Provided kindly by Dr. A. Vogel (1 traj, ca. 11 MB, 528 frames, dt = 50ns)
          For the associated publication see here:

           * Towards Probing Conformational States of Y2 Receptor Using Hyperpolarized 129Xe NMR.
             Schmidt, P.; Vogel, A.; Schwarze, B.; Seufert, F.; Licha, K.; Wycisk, V.; Kilian, W.; Hildebrand, P.W.; Mitschang, L.
             Molecules 2023, 28, 1424. `<https://doi.org/10.3390/molecules28031424>`_

         * mor@muor : https://proteinformatics.uni-leipzig.de/mdciao/muor_199.zip
          Active mu-opioid receptor bound to the agonist morphine (1 traj, ca. 7 MB, 400 frames, dt = 100ns).
          Kindly made available for this purpose by the GPCRmd. The GPCRmd's simulation
          report can be found `here <https://www.gpcrmd.org/dynadb/dynamics/id/199/>`_ ,
          the original publication is:

           * Dynamic and Kinetic Elements of µ-Opioid Receptor Functional Selectivity.
             Kapoor, A., Martinez-Rosell, G., Provasi, D. et al.
             Sci Rep 7, 11255 (2017). `<https://doi.org/10.1038/s41598-017-11483-8>`_

    unzip : bool, or str, default is True
        Try unzipping the file after downloading. If string,
        the url will be downloaded to this filename and then
        unzipped to a folder with this name
        in the working directory, regardless of the
        zipfile's name and internal structure.
    skip_on_existing : bool, default is False
        In case of finding existing files and directories
        skip the downloading and unzipping steps.
        This allows for re-runs w/o being prompted
        for new filenames to avoid overwriting.

    Returns
    -------
    downed_fold_full : str
        The full path to the downloaded data

    """
    # TODO change to proteinformatics.org when ssl problems get fixed
    alias2url = {"b2ar@Gs": "https://proteinformatics.uni-leipzig.de//mdciao/mdciao_example.zip",
                 "EGFR": "https://proteinformatics.uni-leipzig.de/mdciao/example_kinases.zip",
                 "cov19" : "https://proteinformatics.uni-leipzig.de/mdciao/example_cov19.zip",
                 "test": "https://proteinformatics.uni-leipzig.de/mdciao/mdciao_test_small.zip",
                 "ghrelin@ghsr" : "https://proteinformatics.uni-leipzig.de/mdciao/ghrelin_receptor.zip",
                 "mor@muor" : "https://proteinformatics.uni-leipzig.de/mdciao/muor_199.zip",
                 "y1_apo" : "https://proteinformatics.uni-leipzig.de/mdciao/y1_apo.zip"}

    if alias_or_url in alias2url.keys():
        url = alias2url[alias_or_url]
    elif alias_or_url in alias2url.values():
        url = alias_or_url
    else:
        raise ValueError("Cannot find %s in the known aliases or in the known urls:\n%s" % (alias_or_url, alias2url))
    downed_file_full = _down_url_safely(url,
                                        rename_to=[None if isinstance(unzip,bool) else f"{_path.splitext(unzip)[0]}.zip"][0],
                                        skip_on_existing=skip_on_existing)
    if unzip:
        return _unzip2dir(downed_file_full)
    else:
        return  downed_file_full

def _unzip2dir(full_path_zipfile):
    r"""
    Unzip to a folder with the same name as the file, regardless of the structure of the zipfile

    The folder's full path is kept, including zipfile's name minus the .zip extension

    Background: "mdciao_example.zip" was zipped in origin with this structure:
     * mdciao_example/top.pdb
     * mdciao_example/traj.xtc

    However, it might have been renamed to "mdciao_example_05.zip" when auto-downloading.
    If you unzip it directly, it will be extracted to mdciao_example, which ideally
    should be avoided.

    If for whatever reason, mdciao_example_05 *does* exist as a folder, existing files
    will not be overwritten

    Parameters
    ----------
    full_path_zipfile : str
        The zipfile. E.g. "Downloads/mdciao_example_00.zip" will be
        extracted to "Downloads/mdciao_example_00/"

    Returns
    -------
    full_dir : str
        The directory into which the zipfile was extracted

    """
    full_dir = _path.splitext(full_path_zipfile)[0]
    # https://stackoverflow.com/a/56362289
    #local_dir = _path.basename(full_dir)
    print("Unzipping to '%s'" % full_dir)
    with _ZF(full_path_zipfile) as zipdata:
        for zipinfo in zipdata.infolist():
            new = _path.basename(zipinfo.filename)
            zipinfo.filename = new
            if _path.exists(_path.join(full_dir,new)):
                print("No unzipping of '%s': file already exists." % new)
            else:
                zipdata.extract(zipinfo,
                                path=full_dir
                                )
            #assert _path.exists(_path.join(full_dir,new))

    return full_dir

def _down_url_safely(url, chunk_size = 128, verbose=False, rename_to=None, skip_on_existing=False):
    r"""
    Downloads a file from a URL to a tmpfile and copies it to the current directory

    If the file/folder exists already, a new filename is generated using _recursive_prompt

    Parameters
    ----------
    url
    chunk_size
    verbose : bool
        Be verbose
    rename_to : str or None, defoult is None
        Store the downloaded file locally
        under a different name from the
        one it has in the `url`

    Returns
    -------
    filename : str
        The full path to the downloaded filename
    """
    filename_orig = _path.basename(url)
    if rename_to is None:
        target_file = filename_orig
    else:
        target_file = rename_to
    filename_nonx = _recursive_prompt(target_file,
                                      _path.splitext(target_file)[0],
                                      is_file=True, verbose=True, skip_on_existing=skip_on_existing)
    if _path.exists(filename_nonx) and skip_on_existing:
        pass
    else:
        r = _rget(url, stream=True)
        total_size_in_bytes = int(r.headers.get('content-length', 0))
        pb = _tqdma(total=total_size_in_bytes,
                    desc="Downloading %s to %s" % (filename_orig, _path.basename(filename_nonx)))
        with _TDir(suffix="_mdciao_download") as t:
            _filename = _path.join(t,_path.basename(filename_nonx))
            with open(_filename, 'wb') as fd:
                r.iter_content()
                for chunk in r.iter_content(chunk_size=chunk_size):
                    fd.write(chunk)
                    pb.update(128)
            pb.close()
            if verbose:
                print("Dowloaded file %s"%filename_nonx)
            _shcopy(_filename,filename_nonx)

    return filename_nonx

def GPCRLabeler_ardb2_human(**kwargs):
    r"""Build an :obj:`~mdciao.nomenclature.LabelerGPCR` with the adrb2_human.xlsx file shipped with mdciao"""
    return _LabelerGPCR(filenames.adrb2_human_xlsx,**kwargs)

def CGNLabeler_gnas2_human(**kwargs):
    r"""Build an :obj:`~mdciao.nomenclature.LabelerCGN` with the gnas2_human.txt file shipped with mdciao"""
    return _LabelerCGN(filenames.gnas2_human_xlsx,**kwargs)

def Interface_B2AR_Gas(**kwargs):
    r"""
    Return an :obj:`~mdciao.contacts.ContactGroup` object representing a B2AR-Galpha s interface

    Wraps around :obj:`mdciao.cli.interface`

    The input data is one very short (80 frames) version
    of the MD trajectory shipped with mdciao, kindly provided by
    Dr. H. Batebi. See the online examples for more info.

    Parameters
    ----------
    kwargs : keyword args for :obj:`mdciao.cli.interface`

    Returns
    -------
    intf :obj:`~mdciao.contacts.ContactGroup`
    """
    b = _io.StringIO()
    try:
        with _contextlib.redirect_stdout(b):
            example_kwargs = {"topology": filenames.top_pdb,
                              "figures": False,
                              "GPCR_UniProt": GPCRLabeler_ardb2_human(),
                              "CGN_UniProt": CGNLabeler_gnas2_human(),
                              "no_disk": True,
                              "interface_selection_1":[0],
                              "interface_selection_2":[3],
                              "ctc_control":1.0,
                              "accept_guess": True}
            for key, val in kwargs.items():
                example_kwargs[key] = val
            return _interface(filenames.traj_xtc,
                              **example_kwargs,
                              )

    except Exception as e:
        print(b.getvalue())
        b.close()
        raise e

def KLIFSLabeler_P31751() -> _LabelerKLIFS:
    r"""Build an :obj:`~mdciao.nomenclature.LabelerKLIFS` with the KLIFS_P31751.xlsx and 3E8D.pdb.gz.pdb files shipped with mdciao"""
    with _linkorcopy2TDir("_mdciao_example_KLIFS", [filenames.KLIFS_P31751_xlsx, filenames.rcsb_3E8D_pdb]) as t:
        with remember_cwd():
            _chdir(t)
            return _LabelerKLIFS("P31751", try_web_lookup=False)

def AlignerConsensus_B2AR_HUMAN_vs_OPSD_BOVIN() -> _AlignerConsensus:
    r""" Build an :obj:`mdciao.nomenclature.AlignerConsensus` for the B2AR in 3SN6 and the OPS in 3CAP"""
    g3SN6 = _md.load(filenames.rcsb_3SN6_pdb)
    g3CAP = _md.load(filenames.rcsb_3CAP_pdb)

    GPCR_b2ar = GPCRLabeler_ardb2_human()
    GPCR_ops = _LabelerGPCR("OPSD_BOVIN")

    maps = {"B2AR": GPCR_b2ar.top2labels(g3SN6.top),
            "OPS": GPCR_ops.top2labels(g3CAP.top)}

    return _AlignerConsensus(maps, tops={"B2AR": g3SN6.top,
                                         "OPS": g3CAP.top},
                             )
