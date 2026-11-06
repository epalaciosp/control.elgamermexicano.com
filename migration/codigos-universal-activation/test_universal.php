<?php
require __DIR__ . '/universal_activation.php';
$tests = 0;
function check($condition) {
    global $tests;
    ++$tests;
    if (!$condition) { throw new RuntimeException('ASSERTION_FAILED_' . $tests); }
}
// Synthetic value only. Never include a real OTP or mailbox credentials here.
$base = ['sender_email'=>'no-reply@universalplus.com', 'subject'=>'Universal+ Código de activación',
    'content'=>'<p>Tu código de activación</p><strong>Q7W8E9</strong>'];
foreach (['Universal+ Código de activación','UNIVERSAL+ CÓDIGO DE ACTIVACIÓN',
    'Universal+ código de activación',"  Universal+   Código\tde  activación  ",
    "Universal+\u{00A0}Co\u{0301}digo de activacio\u{0301}n"] as $subject) {
    $message = array_replace($base, ['subject'=>$subject]);
    check(universal_activation_matches($message));
    check(universal_activation_code($message) === 'Q7W8E9');
}
foreach (['attacker@example.invalid','no-reply@universalplus.com.invalid','fake-no-reply@universalplus.com',''] as $sender) {
    $message = array_replace($base, ['sender_email'=>$sender]);
    check(!universal_activation_matches($message));
    check(universal_activation_code($message) === null);
}
check(universal_activation_matches(array_replace($base,['sender_email'=>' NO-REPLY@UNIVERSALPLUS.COM '])));
foreach (['Netflix: Your sign-in code','Tu código de acceso único para Disney+',
    'amazon.com: Sign-in attempt','Canva: Your code','Universal+ publicidad'] as $subject) {
    check(!universal_activation_matches(array_replace($base,['subject'=>$subject])));
}
foreach (['ABCDEF','123456','A1B2C3'] as $code) {
    check(universal_activation_code(array_replace($base,['content'=>'<strong>'.$code.'</strong>'])) === $code);
}
foreach (['12345','1234567','abc123','<style>Q7W8E9</style>',
    '<script>Q7W8E9</script>','<div data-code="Q7W8E9">Sin código</div>',
    '<strong>Q7W8E9</strong><strong>A1B2C3</strong>','prefixQ7W8E9suffix',''] as $content) {
    check(universal_activation_code(array_replace($base,['content'=>$content])) === null);
}
check(universal_activation_code(array_replace($base,['content'=>'<b>Q7W8E9</b><b>Q7W8E9</b>'])) === 'Q7W8E9');
check(str_contains(universal_activation_render('Q7W8E9'),'data-universal-code'));
check(!str_contains(universal_activation_render('<img>'),'data-universal-code'));
check(!str_contains(universal_activation_render('Q7W8E9'),'soporte'));
check(universal_activation_code([]) === null);
echo json_encode(['tests'=>$tests,'passed'=>$tests,'fixture_synthetic'=>true,'otp_logged'=>false]) . PHP_EOL;
