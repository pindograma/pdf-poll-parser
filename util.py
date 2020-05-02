# util.py
# (c) 2020 CincoNoveSeis Jornalismo Ltda.
#
# This program is licensed under the GNU General Public License, version 3.
# See the LICENSE file for details.

def as_dec(x):
    return float(x.strip().replace('%', '').replace(',', '.'))

def is_number(x):
    try:
        as_dec(x)
    except ValueError:
        return False
    return True
