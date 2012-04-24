# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support/_mountzlib.py'), os.path.join(CONFIGDIR,'support/useUnicode.py'), '/Users/macdjs/git/CDJSVis/src/CDJSVis.py'],
             pathex=['/Users/macdjs/svn/PyInstaller'],
             hookspath=None)
a.datas += [('data/atoms.IN','/Users/macdjs/git/CDJSVis/src/data/atoms.IN', 'DATA')]
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build/pyi.darwin/CDJSVis', 'CDJSVis'),
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT( exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist', 'CDJSVis'))
app = BUNDLE(coll,
             name=os.path.join('dist', 'CDJSVis.app'),
             version="0.0.1")