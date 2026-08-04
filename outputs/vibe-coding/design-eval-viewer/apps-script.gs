/**
 * AIP 디자인 평가 — 팀 피드백 수집
 *
 * 구글 시트에 붙여넣고 웹 앱으로 배포하면, 평가 뷰어(index.html)의
 * 라이트박스에서 남긴 페이지별 피드백이 이 시트에 한 줄씩 쌓인다.
 *
 * ── 설치 ──────────────────────────────────────────────────────────────
 *  1. 구글 시트를 새로 만든다 (드라이브 위치는 팀 공유 폴더 권장)
 *  2. 확장 프로그램 → Apps Script → 이 파일 내용을 전부 붙여넣고 저장
 *  3. 배포 → 새 배포 → 유형 "웹 앱"
 *       실행 계정 : 나
 *       액세스    : 미리디 내 모든 사용자      ← ★ '모든 사용자'로 하면 작성자를 못 잡는다
 *  4. 나오는 /exec 주소를 index.html 의 SHEET_ENDPOINT 에 붙여넣는다
 *
 * ── 작성자 ────────────────────────────────────────────────────────────
 *  작성자는 브라우저가 보낸 값이 아니라 Session.getActiveUser() 로 서버가 정한다.
 *  즉 뷰어에서 위조할 수 없고, 팀원은 구글에 로그인만 되어 있으면 된다.
 *  (액세스를 '모든 사용자'로 배포하면 이메일이 빈 값으로 들어온다.)
 */

var SHEET_NAME = '피드백';
// '메모' 는 세 칸을 합친 것(한 열만 봐도 읽힌다), 그 뒤 셋은 나중에 층위별로 모으기 위한 분해.
var HEADERS = ['시각', '작성자', '계정', 'designId', '페이지', 'pageUrl', '이미지', 'labels', '메모',
               '바디컴포넌트', '마스터컴포넌트', '그외'];

/** 시트를 확보하고 헤더·서식을 보장한다 */
function sheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  if (sh.getLastRow() === 0) {
    sh.appendRow(HEADERS);
    sh.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold').setBackground('#E7F9FB');
    sh.setFrozenRows(1);
    // 이미지 열이 보이도록 행 높이를 넉넉히 준다
    sh.setColumnWidth(7, 220);
    sh.setColumnWidth(9, 380);
  } else if (sh.getLastColumn() < HEADERS.length) {
    // 메모 3분할 이전에 만든 시트: 뒤에 열 제목만 채워 넣는다.
    // 기존 행은 그대로 두고(합친 '메모' 열에 내용이 있다) 새 행부터 세 열이 찬다.
    var from = sh.getLastColumn() + 1;
    var add = HEADERS.slice(from - 1);
    sh.getRange(1, from, 1, add.length).setValues([add])
      .setFontWeight('bold').setBackground('#E7F9FB');
  }
  return sh;
}

function doPost(e) {
  // 잠금을 쓰지 않는다. 예전엔 '행 번호를 읽고 → 그 행에 수식을 넣는' 두 단계라
  // 동시 저장이 겹치지 않게 잠갔는데, 그 잠금이 몰리면 20초 타임아웃으로 저장이
  // 통째로 실패했다(실측: "잠금 시간초과"). appendRow 는 한 번에 한 행을 원자적으로
  // 붙이고, '=' 로 시작하는 문자열은 수식으로 해석되므로 IMAGE 를 같이 넣으면
  // 두 번째 단계가 필요 없다 → 잠금도 필요 없다.
  try {
    var p = (e && e.parameter) || {};
    if (!p.designId || !p.pageUrl) return out_('designId·pageUrl 이 없습니다', false);

    var who = '';
    try { who = Session.getActiveUser().getEmail() || ''; } catch (err) {}

    var sh = sheet_();
    sh.appendRow([
      new Date(),
      p.author || '',           // 뷰어에서 입력한 이름 (한 번 입력하면 브라우저가 기억)
      who,                      // 구글 계정 — 서버가 정하므로 위조 불가 (감사용)
      p.designId,
      Number(p.pageNo || 0),
      p.pageUrl,
      '=IMAGE("' + String(p.pageUrl).replace(/"/g, '') + '")',
      p.labels || '',
      p.memo || '',                 // 채운 칸을 합친 것
      p.body || '',                 // 바디 컴포넌트
      p.master || '',               // 마스터 컴포넌트
      p.etc || '',                  // 그 외
    ]);

    // 행 높이·줄바꿈은 보기 좋으라고 하는 것 — 실패해도 저장은 성공으로 친다.
    // (동시 저장이 겹치면 다른 행을 꾸밀 수 있지만 데이터에는 영향 없음)
    try {
      var r = sh.getLastRow();
      sh.setRowHeight(r, 130);
      sh.getRange(r, 9).setWrap(true);
    } catch (err2) {}

    return out_('저장했습니다 (' + (p.author || who || '작성자 미확인') + ')', true);
  } catch (err) {
    return out_('오류: ' + err.message, false);
  }
}

/** 배포가 살아있는지 브라우저로 확인할 때 쓴다 */
function doGet() {
  var who = '';
  try { who = Session.getActiveUser().getEmail() || ''; } catch (err) {}
  return out_('정상 동작 중입니다. 로그인 계정: ' + (who || '(확인 안 됨 — 액세스 설정을 미리디 내 모든 사용자로)'), true);
}

/** 뷰어는 숨은 iframe 으로 받으므로 사람이 읽을 수 있는 HTML 로 응답한다 */
function out_(msg, ok) {
  return HtmlService.createHtmlOutput(
    '<p style="font:14px/1.6 sans-serif;color:' + (ok ? '#1C95A2' : '#B42318') + '">' + msg + '</p>');
}
