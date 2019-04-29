import pytest
from agda_kernel.kernel import AgdaKernel
#import agda_kernel.kernel.findAllHoles

@pytest.fixture
def kernel():
    return AgdaKernel()

def test_isHole_1(kernel):
    assert kernel.isHole("?")

def test_isHole_2(kernel):
    assert kernel.isHole("{!!}")

def test_isHole_3(kernel):
    assert kernel.isHole("{! !}")

def test_isHole_4(kernel):
    assert kernel.isHole("{!  !}")

#def test_isHole_5(kernel):
#    assert not kernel.isHole(" {!  !} ")

def test_isHole_6(kernel):
    assert not kernel.isHole(" ?")

def test_isHole_7(kernel):
    assert not kernel.isHole("a")

def test_findAllHoles_1(kernel):
    code = "?"
    result = kernel.findAllHoles(code)
    assert result == [(0,1)]

def test_findAllHoles_2(kernel):
    code = " ? "
    result = kernel.findAllHoles(code)
    assert result == [(1,2)]

def test_findAllHoles_3(kernel):
    code = " ?"
    result = kernel.findAllHoles(code)
    assert result == [(1,2)]

def test_findAllHoles_4(kernel):
    code = "f a b = ?\n f a b = ?"
    result = kernel.findAllHoles(code)
    assert result == [(8,9), (19,20)]

def test_findAllHoles_5(kernel):
    code = "f a b = ?\n f a b = {!!}"
    result = kernel.findAllHoles(code)
    assert result == [(8,9), (19,23)]

def test_findAllHoles_6(kernel):
    code = "f a b = {!  !} f a b = {! !}"
    result = kernel.findAllHoles(code)
    assert result == [(8,14), (23,28)]

def test_findAllHoles_7(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! !} \n\n"
    result = kernel.findAllHoles(code)
    assert result == [(8,14), (43,48)]

def test_findAllHoles_8(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! abc!} \n\n"
    result = kernel.findAllHoles(code)
    assert result == [(8,14), (43,51)]

def test_findCurrentHole_0(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! !} \n\n"
    assert kernel.findCurrentHole(code, 7) == -1

def test_findCurrentHole_1(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! !} \n\n"
    assert kernel.findCurrentHole(code, 8) == 0

def test_findCurrentHole_2(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! !} \n\n"
    assert kernel.findCurrentHole(code, 9) == 0

def test_findCurrentHole_3(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! !} \n\n"
    assert kernel.findCurrentHole(code, 12) == 0

def test_findCurrentHole_4(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! !} \n\n"
    assert kernel.findCurrentHole(code, 13) == 0

def test_findCurrentHole_5(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! !} \n\n"
    assert kernel.findCurrentHole(code, 14) == 0

def test_findCurrentHole_6(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! !} \n\n"
    assert kernel.findCurrentHole(code, 15) == -1

def test_findCurrentHole_7(kernel):
    code = "f a b = {!  !} -- f a b = {! !}  \n f a b = {! !} \n\n"
    assert kernel.findCurrentHole(code, 43) == 1

commentCode = " bla bla bla -- a long comment \n a new line \n-- another comment"

def test_inComment_0(kernel):
    assert not kernel.inComment(commentCode, 12)

def test_inComment_1(kernel):
    assert kernel.inComment(commentCode, 13)

def test_inComment_2(kernel):
    assert kernel.inComment(commentCode, 14)

def test_inComment_3(kernel):
    assert kernel.inComment(commentCode, 30)

def test_inComment_4(kernel):
    assert not kernel.inComment(commentCode, 31)

def test_inComment_5(kernel):
    assert kernel.inComment(commentCode, 45)

def test_inComment_6(kernel):
    assert kernel.inComment(commentCode, 46)

def test_removeComments_0(kernel):
    assert kernel.removeComments("hello -- comments\nhey") == "hello \nhey"

def test_removeComments_1(kernel):
    assert kernel.removeComments("hello -- comments {- {- \nhey{- oy{- hey-}-}go") == "hello \nheygo"

def test_removeComments_2(kernel):
    assert kernel.removeComments("a {- -- this comments ends earlier {- \nhey hey-}  -} line") == "a  line"

def test_removeComments_3(kernel):
    assert kernel.removeComments("a {- -- this comments ends earlier {- \nhey hey-}  -} -} line") == "a  -} line"

def test_removeComments_4(kernel):
    assert kernel.removeComments("a {- -- this comments ends earlier {- \nhey hey-}   line-}") == "a "

def test_getModuleName_0(kernel):
    assert kernel.getModuleName("module pippo where \n \n paperino and pluto") == "pippo"
        
def test_getModuleName_1(kernel):
    assert kernel.getModuleName("\n \nmodule pippo where \n \n paperino and pluto") == "pippo"

def test_getModuleName_2(kernel):
    assert kernel.getModuleName("\n {-# PRAGMA bla bla  #-} \nmodule pippo where \n \n paperino and pluto") == "pippo"

def test_getModuleName_3(kernel):
    assert kernel.getModuleName("\n \n {-# PRAGMA bla bla  #-}\n {-module sandokan where-} \n -- module pluto where \nmodule pippo where \n \n paperino and pluto") == "pippo"

def test_getModuleName_4(kernel):
    assert kernel.getModuleName("module pippo where   \n") == "pippo"

def test_auto_all_results(kernel):
    assert kernel.do_complete("module test where\nh : {A : Set} → A → A → A\nh x y = ?", 52)['matches'] == ["y", "x"]
