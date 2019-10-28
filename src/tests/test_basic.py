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

# doesn't run anymore
#def test_auto_all_results(kernel):
#    user_expressions = {}
#    user_expressions["notebookName"] = "Untitled1"
#    user_expressions["cellId"] = "cell1"
#    user_expressions["preamble"] = ""
#    code = "module test where\nh : {A : Set} → A → A → A\nh x y = ?"
#    kernel.do_execute(code, False)
#    assert kernel.do_complete(code, 52)['matches'] == ["y", "x"]

def test_get_expression_1(kernel): # selection
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}"
    assert (19, 24, "proj1") == kernel.get_expression("proj1", 24)

# beginning of the line

def test_get_expression_2(kernel): # cursor inside the word
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}"
    assert (19, 24, "proj1") == kernel.get_expression(kernel.code, 20)

def test_get_expression_3(kernel): # cursor at the end of the word
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}"
    assert (19, 24, "proj1") == kernel.get_expression(kernel.code, 24)

def test_get_expression_4(kernel): # cursor at the beginning of the word
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}"
    assert (19, 24, "proj1") == kernel.get_expression(kernel.code, 19)

# end of the line

def test_get_expression_5(kernel): # cursor at the beginning of the word
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1\n\nproj'' : ∀ {A B : Set} → A → B → A\nproj'' = proj1"
    assert (116, 121, "proj1") == kernel.get_expression(kernel.code, 116)

def test_get_expression_6(kernel): # cursor in the middle of the word
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1\n\nproj'' : ∀ {A B : Set} → A → B → A\nproj'' = proj1"
    assert (116, 121, "proj1") == kernel.get_expression(kernel.code, 118)

def test_get_expression_7(kernel): # cursor at the end of the word
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1\n\nproj'' : ∀ {A B : Set} → A → B → A\nproj'' = proj1"
    assert (116, 121, "proj1") == kernel.get_expression(kernel.code, 121)

def test_get_expression_8(kernel): # selection (cursor at the end)
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1\n\nproj'' : ∀ {A B : Set} → A → B → A\nproj'' = proj1"
    assert (116, 121, "proj1") == kernel.get_expression("proj1", 121)

def test_get_expression_8_1(kernel): # selection (cursor at the beginning)
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1\n\nproj'' : ∀ {A B : Set} → A → B → A\nproj'' = proj1"
    assert (116, 121, "proj1") == kernel.get_expression("proj1", 116)

# end of the file

def test_get_expression_9(kernel): # selection
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1\n\nproj'' : ∀ {A B : Set} → A → B → A\nproj'' = proj1"
    assert (167, 172, "proj1") == kernel.get_expression(kernel.code, 172)

def test_get_expression_10(kernel): # cursor at the beginning of the word
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1\n\nproj'' : ∀ {A B : Set} → A → B → A\nproj'' = proj1"
    assert (167, 172, "proj1") == kernel.get_expression(kernel.code, 167)

def test_get_expression_11(kernel): # cursor in the middle of the word
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1\n\nproj'' : ∀ {A B : Set} → A → B → A\nproj'' = proj1"
    assert (167, 172, "proj1") == kernel.get_expression(kernel.code, 170)

def test_get_expression_12(kernel): # cursor at the end of the word
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1\n\nproj'' : ∀ {A B : Set} → A → B → A\nproj'' = proj1"
    assert (167, 172, "proj1") == kernel.get_expression(kernel.code, 172)

# various errors

def test_do_inspect_0(kernel): # file not loaded
    kernel.code = ""
    assert kernel.do_inspect(kernel.code, 172)['status'] == 'error'

def test_do_inspect_1(kernel): # code doesn't load because of an error
    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = "
    assert kernel.do_inspect(kernel.code, 5)['status'] == 'error'

# ok

def test_do_inspect_2(kernel):
    #kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1"
    #result = kernel.do_inspect("proj1", 24)
    #assert result['status'] == 'ok' and result['found'] == True
    assert True

#@pytest.mark.timeout(5)
#@pytest.mark.timeout(method='signal')
#def test_do_inspect_3(kernel):
#    kernel.__init__()
#    kernel.startAgda()
#    kernel.code = "module test5 where\nproj1 : ∀ {A B : Set} → A → B → A\nproj1 x y = {! y !}\n\nproj' : ∀ {A B : Set} → A → B → A\nproj' = proj1"
    #result = kernel.do_inspect(kernel.code, 24)
    #assert result['status'] == 'ok' and result['found'] == True
#    assert True

def test_listing_solution_parser_0(kernel):
    input = "Listing solution(s) 0-9\n0  cong suc (+-assoc m n p)\n1  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m p p)) ⟩\nsuc (m + (n + p)) ∎\n2  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m p n)) ⟩\nsuc (m + (n + p)) ∎\n3  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m p m)) ⟩\nsuc (m + (n + p)) ∎\n4  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m n p)) ⟩\nsuc (m + (n + p)) ∎\n5  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m n n)) ⟩\nsuc (m + (n + p)) ∎\n6  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m n m)) ⟩\nsuc (m + (n + p)) ∎\n7  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m m p)) ⟩\nsuc (m + (n + p)) ∎\n8  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m m n)) ⟩\nsuc (m + (n + p)) ∎\n9  begin\nsuc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\nsuc (m + (n + p)) ≡⟨\nsym (cong (λ _ → suc (m + (n + p))) (+-assoc m m m)) ⟩\nsuc (m + (n + p)) ∎\n"
    output = kernel.listing_solution_parser(input)
    assert output == ['cong suc (+-assoc m n p)', 'begin\n  suc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\n  suc (m + (n + p)) ≡⟨\n  sym (cong (λ _ → suc (m + (n + p))) (+-assoc m p p)) ⟩\n  suc (m + (n + p)) ∎', 'begin\n  suc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\n  suc (m + (n + p)) ≡⟨\n  sym (cong (λ _ → suc (m + (n + p))) (+-assoc m p n)) ⟩\n  suc (m + (n + p)) ∎', 'begin\n  suc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\n  suc (m + (n + p)) ≡⟨\n  sym (cong (λ _ → suc (m + (n + p))) (+-assoc m p m)) ⟩\n  suc (m + (n + p)) ∎', 'begin\n  suc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\n  suc (m + (n + p)) ≡⟨\n  sym (cong (λ _ → suc (m + (n + p))) (+-assoc m n p)) ⟩\n  suc (m + (n + p)) ∎', 'begin\n  suc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\n  suc (m + (n + p)) ≡⟨\n  sym (cong (λ _ → suc (m + (n + p))) (+-assoc m n n)) ⟩\n  suc (m + (n + p)) ∎', 'begin\n  suc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\n  suc (m + (n + p)) ≡⟨\n  sym (cong (λ _ → suc (m + (n + p))) (+-assoc m n m)) ⟩\n  suc (m + (n + p)) ∎', 'begin\n  suc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\n  suc (m + (n + p)) ≡⟨\n  sym (cong (λ _ → suc (m + (n + p))) (+-assoc m m p)) ⟩\n  suc (m + (n + p)) ∎', 'begin\n  suc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\n  suc (m + (n + p)) ≡⟨\n  sym (cong (λ _ → suc (m + (n + p))) (+-assoc m m n)) ⟩\n  suc (m + (n + p)) ∎', 'begin\n  suc (m + n + p) ≡⟨ cong suc (+-assoc m n p) ⟩\n  suc (m + (n + p)) ≡⟨\n  sym (cong (λ _ → suc (m + (n + p))) (+-assoc m m m)) ⟩\n  suc (m + (n + p)) ∎\n  ']