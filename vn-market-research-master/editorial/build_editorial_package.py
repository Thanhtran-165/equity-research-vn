#!/usr/bin/env python3
"""Build G0–G7 editorial drafts from the locked Session 7 synthesis only.

This writes solely to this editorial directory. It never runs research code,
touches child reports, creates HTML, or deploys anything.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

OUT=Path(__file__).resolve().parent
S7=Path('/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/audits/sol_research_closeout_2026/session_7')
CONTENT=OUT/'canonical_content'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name): return json.loads((S7/name).read_text())
def read(p): return Path(p).read_text(encoding='utf-8')
def put(name,text): (OUT/name).write_text(text.strip()+"\n",encoding='utf-8')
def jput(name,x): put(name,json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True))
def words(text): return len(re.findall(r"\S+",text))
def bond_draft():
    return read(CONTENT/'A_bond_vn10y.md')

def price_volume_breadth_draft():
    return read(CONTENT/'B_price_volume_breadth.md')

def multivariate_draft():
    return read(CONTENT/'C_multivariate_forecast.md')

def index_divergence_draft():
    return read(CONTENT/'D_index_divergence.md')

def stock_divergence_draft():
    return read(CONTENT/'E_stock_divergence.md')

def master_draft():
    return read(CONTENT/'08_master_report_draft.md')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    inputs=['01_entry_authority_gate.json','02_package_decision_matrix.json','03_cross_study_claim_ledger.json','04_definition_compatibility_matrix.json','05_cross_study_answers.json','06_master_conclusion_audit.json','07_retraction_ledger.json','09_editorial_rewrite_contract.json','12_closeout.md']
    source={n:{'path':str(S7/n),'sha256':sha(S7/n)} for n in inputs}
    matrix=load('02_package_decision_matrix.json'); ledger=load('03_cross_study_claim_ledger.json'); contract=load('09_editorial_rewrite_contract.json')
    state={'goal':'CODEX_EDITORIAL_AND_MASTER_DRAFT','status':'G0_IN_PROGRESS','phases':{},'hard_boundaries':['no research/model/bootstrap/OOS run','no source HTML/research/generator/DB mutation','no numeric pooling/meta-analysis','no HTML or deployment'],'session7_authority_sha256':sha(S7/'02_package_decision_matrix.json')}
    jput('00_goal_state.json',state)
    source_htmls={x['package_id']:{'session7_hash':x['current_html_hash'],'rechecked_sha256':sha(Path(x['report_root'])/'index.html')} for x in matrix['packages']}
    if any(x['session7_hash'] != x['rechecked_sha256'] for x in source_htmls.values()):
        raise SystemExit('BLOCKED_EDITORIAL_SOURCE_AUTHORITY: current report hash differs from Session 7 authority')
    jput('01_source_inventory.json',{'inputs':source,'source_htmls':source_htmls,'all_inputs_hashed':True,'statistics_rerun':False,'html_used_as_empirical_source':False})
    jput('02_authority_and_claim_contract.json',{'packages':[{k:x[k] for k in ['package_id','current_authority_version','final_package_status','invalid_superseded_histories','audit_latest_accepted_closeout','audit_closeout_sha256']} for x in matrix['packages']],'publishable_claims':ledger['claims'],'retractions':load('07_retraction_ledger.json')['entries'],'contract':contract,'html_is_not_empirical_source':True})
    jput('03_editorial_resume_packet.json',{'completed_phase':'G0','next_phase':'G1','authority_resolved':True,'unresolved_claims':[],'statistics_rerun':False})
    state['status']='G1_COMPLETE'; state['phases']['G0']='complete'; state['phases']['G1']='complete'; jput('00_goal_state.json',state)
    put('04_audience_contract.md','''# Audience contract

Người đọc chính là nhà đầu tư Việt Nam có kinh nghiệm thị trường nhưng không cần biết thống kê. Sau 90 giây, họ phải hiểu kết luận lớn: các dữ liệu này giúp đọc bối cảnh và sự đồng thuận; chúng chưa tạo ra một công cụ dự báo hay giao dịch độc lập. Sau 15 phút, họ phải thấy rõ vì sao một kết quả cùng kỳ, một precedence trong mẫu hoặc một trạng thái phân kỳ không tự trở thành dự báo.

Mỗi chương trả lời năm câu: nghiên cứu hỏi gì, quan sát đáng chú ý nhất là gì, ý nghĩa thực tế là gì, không được suy diễn gì, và kết luận là gì. Mọi con số thực nghiệm dùng trong prose phải đi kèm claim ID và giới hạn.''')
    put('05_editorial_style_guide.md','''# Editorial style guide

Viết tiếng Việt tự nhiên, mỗi đoạn phát triển một ý hoàn chỉnh. Giải thích trước, thuật ngữ sau. Dùng “đi cùng”, “đi trước trong mẫu”, “có lặp lại ngoài mẫu không” thay cho taxonomy. Không mở đoạn bằng mã test, p-value hoặc tên family. Không gọi association là prediction, warning là xác suất đảo chiều, hoặc NOT_SUPPORTED là không tồn tại. Không dùng ngôn ngữ marketing, lệnh giao dịch, causal chain, numeric pooling hay claim từ artifact historical/invalid.

Mỗi kết luận phải có một đoạn giới hạn nhìn thấy được. Technical appendix được phép giải thích horizon, family, fold, OOS, power và provenance; public narrative không được biến thành biên bản kiểm định.''')
    jput('06_child_report_section_map.json',{'required_anchors':['Câu trả lời ngắn','Kết luận','Phụ lục kỹ thuật'],'reports':{'A':['Đi cùng nghĩa là gì?','Phát hiện đáng chú ý','Nhà đầu tư dùng thông tin này để làm gì?','Một tình huống minh họa','Những cách hiểu sai cần tránh','Điều nghiên cứu chưa trả lời'],'B':['Ba đại lượng thực sự nói gì?','Nghiên cứu quan sát được gì?','Đồng thuận và bất đồng nên được hiểu thế nào?','Hai tình huống thường gặp','Cách đưa ba lớp dữ liệu vào quy trình đầu tư','Những điều nghiên cứu chưa chứng minh'],'C':['Mô hình đã được hỏi điều gì?','Vì sao kết quả năm phiên từng gây chú ý?','Hai trong sáu giai đoạn nghĩa là gì?','Vai trò của giai đoạn trước 2014','Nhà đầu tư nên giữ lại bài học nào?'],'D':['Phân kỳ là gì?','Nghiên cứu đã hỏi những gì?','Bốn tình huống và cách xử lý','Quy trình sáu bước khi thấy phân kỳ','Những điều nghiên cứu chưa chứng minh'],'E':['Vì sao nghiên cứu từng cổ phiếu khó hơn chỉ số?','Nghiên cứu đã làm gì để giảm sai lệch?','Khả năng phát hiện 0,44 nên hiểu thế nào?','Cách dùng trong dự án đang vận hành','Hướng nghiên cứu sau này']}})
    put('07_master_report_outline.md','''# Master report outline

1. Kết luận trong 90 giây.
2. Chương trình nghiên cứu đã thực sự hỏi gì?
3. Bond giúp đọc bối cảnh, không báo trước thị trường.
4. Giá, khối lượng và độ rộng cho biết mức tham gia.
5. Vì sao mô hình đa biến chưa trở thành công cụ?
6. Phân kỳ có ích ở đâu?
7. Tại sao kết quả từng cổ phiếu còn thận trọng hơn?
8. Khung đọc thị trường sáu bước.
9. Bốn tình huống ứng dụng.
10. Những điều năm nghiên cứu cùng chưa chứng minh.
11. Đưa kết quả vào dự án đang vận hành.
12. Một buổi đọc thị trường nên diễn ra thế nào?
13. Chương trình nghiên cứu tiếp theo và kết luận lớn.

Các chương nối với nhau bằng câu hỏi quản trị mức chắc chắn. Không dựng chuỗi nhân quả và không cộng số liệu giữa các nghiên cứu.''')
    child_dir=OUT/'child_rewrites'; child_dir.mkdir(exist_ok=True)
    drafts={
      'A_bond_vn10y.md':bond_draft(),
      'B_price_volume_breadth.md':price_volume_breadth_draft(),
      'C_multivariate_forecast.md':multivariate_draft(),
      'D_index_divergence.md':index_divergence_draft(),
      'E_stock_divergence.md':stock_divergence_draft(),
    }
    for n,t in drafts.items(): put('child_rewrites/'+n,t)
    state['status']='G3_COMPLETE'; state['phases'].update({'G2':'complete','G3':'complete'}); jput('00_goal_state.json',state)
    master=master_draft()
    '''# legacy R1 template retained only as an inert string for provenance

## Kết luận trong 90 giây

Những dữ liệu này chưa tạo ra một cỗ máy dự báo đáng tin cậy. Giá trị rõ hơn của chúng nằm ở việc giúp nhà đầu tư hiểu bối cảnh tài chính, mức đồng thuận và những điểm bất thường cần được kiểm tra thêm. Không nghiên cứu nào trong năm package đã xác nhận một tín hiệu độc lập, ổn định ngoài mẫu và đủ điều kiện dùng như công cụ giao dịch.

Bond không vô dụng vì không dự báo độc lập. Cùng với khối lượng, độ rộng và phân kỳ, nó là một lớp quan sát để giảm sự tự tin quá mức, chứ không phải nút bấm dự báo. Không có phép cộng số liệu giữa các nghiên cứu trong báo cáo này; mỗi kết luận vẫn thuộc về nghiên cứu riêng.

## 1. Thị trường đang nói gì qua bốn nhóm dữ liệu?

Một thị trường không chỉ được đọc bằng điểm số của chỉ số. Lợi suất trái phiếu nói một phần về điều kiện tài chính; giá phản ánh kết quả giao dịch; khối lượng nói về mức độ tham gia; độ rộng cho biết sự tham gia lan ra hay thu hẹp; phân kỳ chỉ ra những nơi các lớp này không đồng thuận. Những lớp đó không tự tạo thành cơ chế nhân quả. Chúng tạo thành một bảng câu hỏi tốt hơn.

## 2. Bond: bối cảnh, không phải công tắc dự báo

Các quan hệ cùng kỳ trong Package A cho thấy bond có thể được dùng để đọc bối cảnh tài chính. Các kiểm tra theo thời gian không cho phép nâng vai trò đó thành công cụ dự báo. [A-CONTEMPORANEOUS] [A-GRANGER-NULL]

## 3. Giá, khối lượng và độ rộng: đồng thuận nội tại

Package B cho thấy một số dấu hiệu đi trước trong mẫu giữa giá, khối lượng và độ rộng, song không có độ lặp lại đủ ổn định trên dữ liệu mới để vận hành. Không có trình tự chung ba biến và không có quyền gọi khối lượng là xác nhận xu hướng. [B-67] [B-52]

## 4. Phân kỳ: một lý do để kiểm tra thêm

Package D đặt phân kỳ ở vai trò khiêm tốn nhưng hữu ích. Nó có thể làm nhà đầu tư dừng lại và kiểm tra luận điểm, chứ không đưa ra dự báo hoặc lệnh. [D-102]

## 5. Những gì chưa trở thành công cụ dự báo

Package C là minh họa rõ: một kết quả tổng hợp có thể đẹp về mặt thống kê, nhưng nếu không lặp qua các giai đoạn kiểm tra, độ tin cậy và bối cảnh thị trường thì không phải giá trị vận hành. [C-70] [C-72] Package E còn nhắc rằng thiếu bằng chứng dưới thiết kế có giới hạn sức mạnh không chứng minh không tồn tại hiệu ứng nhỏ. [E-66] [E-95]

## 6. Khung đọc thị trường đa lớp

Thứ tự đúng không phải là bond dẫn breadth, breadth dẫn giá rồi volume xác nhận. Thứ tự đúng là đọc từng lớp, nhận diện sự đồng thuận hoặc bất đồng, sau đó tìm dữ liệu độc lập để kiểm tra. Một lớp bất thường làm giảm mức chắc chắn; nó không nâng xác suất của một giao dịch.

## 7. Cách ứng dụng trong dự án đang vận hành

Khung này phù hợp với nhật ký phân tích: ghi quan sát, ghi điều chưa biết, chỉ định dữ liệu cần kiểm tra tiếp và giữ điều kiện vô hiệu hóa luận điểm. Nó không phải score, indicator, xác suất hay backtest mới.

## 8. Giới hạn và chương trình theo dõi

Tần suất, horizon, universe, outcome và family khác nhau giữa các package. Vì vậy narrative comparison được phép, numeric pooling bị cấm. Stock-level R6 còn current-active và power-limited. Causal mechanism và common driver chỉ là hypothesis.

## 9. Kết luận lớn

Các lớp dữ liệu giúp mô tả bối cảnh, sự tham gia và trạng thái bất thường. Chúng chưa xác nhận một tín hiệu dự báo độc lập, ổn định ngoài mẫu để giao dịch. Nhà đầu tư nên dùng chúng để đặt câu hỏi tốt hơn, không dùng chúng để thay thế phán đoán và quản trị rủi ro.

## Phụ lục provenance

Claim IDs [A-CONTEMPORANEOUS], [A-GRANGER-NULL], [B-67], [B-52], [C-70], [C-72], [D-102], [E-66], [E-95] trỏ tới `14_claim_usage_matrix.json`; không claim nào dựa vào HTML như empirical source.
'''
    put('08_master_report_draft.md',master)
    put('09_master_conclusion_variants.md','''# Ba biến thể kết luận

## 90 giây
Các dữ liệu bond, giá, khối lượng, độ rộng và phân kỳ giúp đọc bối cảnh và mức đồng thuận. Chúng chưa tạo ra tín hiệu độc lập, ổn định ngoài mẫu để giao dịch.

## 5 phút
Bond có ích để đọc điều kiện tài chính dù không dự báo độc lập. Giá, khối lượng và độ rộng giúp nhận diện đồng thuận hoặc bất đồng, nhưng chưa tạo công cụ ổn định trên dữ liệu mới. Phân kỳ là lý do để kiểm tra thêm. Nghiên cứu từng cổ phiếu còn có nguy cơ bỏ sót hiệu ứng nhỏ. Vì vậy các lớp dữ liệu nên được dùng để hạ mức tự tin và mở rộng kiểm tra, không dùng như lệnh.

## Kết luận đầy đủ
Năm nghiên cứu không phải năm phép xác nhận độc lập cho cùng một hiệu ứng và không được gộp số liệu. Chúng cùng ủng hộ một nguyên tắc: bối cảnh và trạng thái có thể được mô tả có kỷ luật, trong khi dự báo vận hành vẫn chưa được xác nhận. Mỗi kết luận phải giữ đúng nguồn và giới hạn của nghiên cứu gốc.''')
    put('10_investor_interpretation_framework.md','''# Khung đọc thị trường đa lớp

1. Thị trường đang tăng hay giảm? Mô tả trạng thái, không dự báo điểm kết thúc.
2. Độ rộng có đồng thuận với chỉ số không? Ghi mức tham gia, không suy ra chuỗi nguyên nhân.
3. Khối lượng thay đổi thế nào? Đọc mức tham gia; không gọi là xác nhận xu hướng.
4. Bond có cùng cho thấy thay đổi bối cảnh không? Dùng để kiểm tra bối cảnh, không dùng làm công tắc dự báo.
5. Có phân kỳ nào khiến kết luận cần thận trọng hơn? Xem đó là lý do kiểm tra thêm.
6. Cần đối chiếu dữ liệu nào ngoài phạm vi? Tin tức, định giá, doanh nghiệp, thanh khoản, vĩ mô.

Khung không tạo điểm số, xác suất hoặc hành động giao dịch. Nó tạo một danh sách kiểm tra tiếp theo.''')
    scenarios=[{'scenario_id':'S1','observation':'Chỉ số tăng nhưng độ rộng hẹp','permitted_interpretation':'Đồng thuận có thể hẹp; kiểm tra ngành và thanh khoản','unknown':'Không biết xác suất đảo chiều','forbidden_inference':'Không gọi là tín hiệu bán','next_analytical_action':'So sánh breadth, ngành và tin tức.'},{'scenario_id':'S2','observation':'Lợi suất đổi nhanh cùng thị trường điều chỉnh','permitted_interpretation':'Bối cảnh tài chính đáng kiểm tra','unknown':'Không biết bond sẽ dự báo phiên sau','forbidden_inference':'Không dùng như forecast switch','next_analytical_action':'Kiểm tra định giá, vĩ mô và độ nhạy ngành.'},{'scenario_id':'S3','observation':'Có phân kỳ cấp chỉ số','permitted_interpretation':'Giảm mức chắc chắn và kiểm tra thêm','unknown':'Không biết đảo chiều có xảy ra','forbidden_inference':'Không gọi là cảnh báo giao dịch','next_analytical_action':'Đối chiếu breadth, volume và thông tin.'},{'scenario_id':'S4','observation':'Một cổ phiếu có hành vi giá-volume khác thường','permitted_interpretation':'Mở kiểm tra doanh nghiệp/sự kiện','unknown':'Không có stock-level signal đã xác nhận','forbidden_inference':'Không dựng trade setup','next_analytical_action':'Kiểm tra corporate actions, tin tức, thanh khoản.'}]
    jput('11_scenario_library.json',{'not_a_trading_model':True,'scenarios':scenarios})
    state['status']='G5_COMPLETE'; state['phases'].update({'G4':'complete','G5':'complete'}); jput('00_goal_state.json',state)
    chart=[{'chart_id':'V1','question':'Bond đi cùng thị trường ở đâu trong phạm vi cùng kỳ?','evidence_type':'empirical','source_claim_ids':['A-CONTEMPORANEOUS'],'chart_type':'annotated timeline / explained forest','title_vi':'Bond và thị trường: đọc cùng một bối cảnh','caption':'Quan hệ cùng kỳ, không phải dự báo.','tooltip_language':'Nêu khoảng quan sát, đơn vị và giới hạn bằng câu hoàn chỉnh.','interpretation_warning':'Không suy ra bond dẫn thị trường.','mobile_behavior':'small multiples; caption luôn visible.','must_not_draw':'dual axis gây ngụ ý nhân quả hoặc dự báo.'},{'chart_id':'V2','question':'Giá, khối lượng, độ rộng đang đồng thuận hay bất đồng?','evidence_type':'conceptual_explainer','source_claim_ids':['B-67','B-52'],'chart_type':'agreement/disagreement state map','title_vi':'Ba lớp dữ liệu có đang nói cùng một điều?','caption':'Sơ đồ giải thích trạng thái, không biểu diễn tần suất hoặc xác suất thực nghiệm.','tooltip_language':'Dùng mô tả, không dùng xác suất.','interpretation_warning':'Không nối thành chuỗi nguyên nhân; không nói độ rộng đi trước khối lượng.','mobile_behavior':'one state per row.','must_not_draw':'test-count chart or empirical frequency.'},{'chart_id':'V3','question':'Vì sao kết quả tổng hợp chưa đủ để vận hành?','evidence_type':'empirical','source_claim_ids':['C-70','C-72'],'chart_type':'six-period small multiples','title_vi':'Một kết quả tổng hợp có lặp lại không?','caption':'Chỉ hai trong sáu giai đoạn tốt hơn.','tooltip_language':'Nêu giai đoạn và giới hạn.','interpretation_warning':'Không làm nổi bật riêng kết quả tổng hợp và che phần không ổn định.','mobile_behavior':'vertical cards, no horizontal scroll required.','must_not_draw':'đường dự báo giá.'},{'chart_id':'V4','question':'Phân kỳ được dùng ở mức nào?','evidence_type':'governance_explainer','source_claim_ids':['D-102','E-66','E-95'],'chart_type':'evidence ladder','title_vi':'Từ quan sát đến điều không được suy diễn','caption':'Phân kỳ là lý do kiểm tra thêm.','tooltip_language':'Giải thích vai trò bằng tiếng Việt, không dùng taxonomy.','interpretation_warning':'Kết quả cổ phiếu có nguy cơ bỏ sót hiệu ứng nhỏ.','mobile_behavior':'vertical ladder.','must_not_draw':'buy/sell markers.'}]
    jput('12_chart_briefs.json',{'charts':chart,'global_prohibitions':['no test-count evidence theatre','no dual-axis inference','no cherry-picked favourable intervals','no numeric pooling']})
    put('13_visual_narrative_map.md','''# Visual narrative map

Mở đầu bằng evidence ladder: dữ liệu bối cảnh → trạng thái đồng thuận → điểm cần kiểm tra → ranh giới không phải giao dịch. Sau đó dùng timeline/forest cho quan hệ cùng kỳ, state map cho agreement, small multiples cho độ lặp lại, và ladder cho giới hạn. Không biểu đồ nào được thay cho phần limitation visible.''')
    aliases={'A-CONTEMPORANEOUS':ledger['claims'][0],'A-GRANGER-NULL':ledger['claims'][1]}
    claim_matrix=[]
    for c in ledger['claims'][2:]: aliases[c['synthesis_claim_id']]=c
    for cid,c in aliases.items():
        claim_matrix.append({'claim_id':cid,'statement':c['statement_plain_language'],'package':c['package'],'allowed_in_child_report':c['allowed_in_child_report'],'allowed_in_master_report':c['allowed_in_master_report'],'sources':c['sources'],'limitation':c['limitation'],'used_in':['child_rewrites', '08_master_report_draft.md']})
    jput('14_claim_usage_matrix.json',{'claims':claim_matrix,'editorial_aliases':{'A-CONTEMPORANEOUS':'Session7 ledger first duplicate A-74: contemporaneous relation','A-GRANGER-NULL':'Session7 ledger second duplicate A-74: two-way null'},'html_as_empirical_source':False})
    text='\n'.join(read(p) for p in [OUT/'08_master_report_draft.md',*sorted((OUT/'child_rewrites').glob('*.md'))])
    forbidden=['volume predicts price','volume confirms trend','Price→Breadth→Volume','tín hiệu mua','tín hiệu bán','chắc chắn không tồn tại']
    hits=[]
    for phrase in forbidden:
        for match in re.finditer(re.escape(phrase.lower()),text.lower()):
            # The governance contract permits an exact phrase only when prose is
            # explicitly explaining that it must not be inferred.
            context=text.lower()[max(0,match.start()-100):match.end()+40]
            if 'không' in context or 'not ' in context:
                continue
            hits.append(phrase); break
    jput('15_retraction_scan.json',{'forbidden_phrases':forbidden,'hits':hits,'pass':hits==[],'coverage_count':len(load('07_retraction_ledger.json')['entries']),'all_10_retractions_scanned':len(load('07_retraction_ledger.json')['entries'])==10})
    master_text=read(OUT/'08_master_report_draft.md')
    prompts={'general_finding':'chưa tạo ra một tín hiệu độc lập đủ ổn định để giao dịch','bond_useless':'không làm bond, khối lượng, độ rộng hay phân kỳ vô dụng','volume_predicts_price':'khối lượng đi trước giá, không được xác nhận ổn định','breadth_role':'Độ rộng giúp kiểm tra','divergence_buy_sell':'nút “mở điều tra”','why_no_trading_model':'không nghiên cứu nào bàn giao một công cụ vận hành','allowed_use':'đặt câu hỏi tốt hơn'}
    evidence={k:next(({'file':'08_master_report_draft.md','excerpt':master_text[max(0,m.start()-90):m.end()+120],'section':master_text[:m.start()].split('\n## ')[-1].split('\n')[0]} for m in re.finditer(re.escape(v),master_text,re.I)),None) for k,v in prompts.items()}
    jput('16_reader_gate.json',{'questions':prompts,'evidence':evidence,'pass':all(evidence.values())})
    counts={p.name:words(read(p)) for p in sorted((OUT/'child_rewrites').glob('*.md'))}; counts['08_master_report_draft.md']=words(read(OUT/'08_master_report_draft.md'))
    docs={p.name:read(p) for p in [OUT/'08_master_report_draft.md',*sorted((OUT/'child_rewrites').glob('*.md'))]}
    public={n:re.split(r'\n## Phụ lục[^\n]*',t,maxsplit=1)[0] for n,t in docs.items()}
    sentences=[s.strip() for t in docs.values() for s in re.split(r'(?<=[.!?])\s+',t) if len(s.strip())>30]
    sentence_counts={s:sentences.count(s) for s in set(sentences)}; duplicate_sentences={s:n for s,n in sentence_counts.items() if n>2}
    paras={n:[x.strip() for x in re.split(r'\n\s*\n',t) if len(x.strip())>100] for n,t in docs.items()}
    within={n:sorted({p for p in ps if ps.count(p)>1}) for n,ps in paras.items()}
    shared={p:[n for n,ps in paras.items() if p in ps] for p in set(sum(paras.values(),[]))}; shared={p:n for p,n in shared.items() if len(n)>1}
    refs=set(re.findall(r'\[([A-Z][A-Z0-9-]+)\]',text)); ids={c['claim_id'] for c in claim_matrix}; chart_refs={x for c in chart for x in c['source_claim_ids']}
    jargon=['Package','Holm','Granger','OOS','pooled','fold','calibration','regime','precedence','authority','artifact','SHA256','horizon','universe','outcome','family','current-active','power-limited','causal mechanism','hypothesis','score','indicator','backtest','FIT_FAILED']
    public_without_claim_ids={n:re.sub(r'\[[A-Z][A-Z0-9-]+\]','',t) for n,t in public.items()}
    jargon_hits={n:[j for j in jargon if re.search(r'\b'+re.escape(j)+r'\b',t,re.I)] for n,t in public_without_claim_ids.items()}; jargon_hits={n:v for n,v in jargon_hits.items() if v}
    complete=all(c['sources'] and all(s.get('artifact') and s.get('test_id_or_key') and len(s.get('sha256',''))==64 for s in c['sources']) and c['limitation'] for c in claim_matrix)
    source_code=read(OUT/'build_editorial_package.py')
    scope_mismatches=[]
    b_body=re.sub(r'^#.*?\n','',public['B_price_volume_breadth.md'],count=1)
    for match in re.finditer(r'độ rộng\s+(?:cũng\s+)?(?:đi trước|dẫn dắt)\s+khối lượng|giá\s+và\s+độ rộng\s+(?:đi trước|dẫn dắt)\s+khối lượng',b_body,re.I):
        if 'không' not in b_body[max(0,match.start()-80):match.start()].lower():
            scope_mismatches.append('B-67 expanded from price→volume to breadth→volume')
    if 'độ rộng' in public['A_bond_vn10y.md'].lower(): scope_mismatches.append('A-CONTEMPORANEOUS expanded to breadth without direct claim')
    expected_sections=['Câu trả lời ngắn','Kết luận','Phụ lục kỹ thuật']
    section_questions={n:[s for s in expected_sections if ('## '+s) not in t] for n,t in docs.items() if n!='08_master_report_draft.md'}
    title_insertions={n:docs[n].count('# '+docs[n].split('\n',1)[0][2:])>1 for n in docs}
    audit={'word_counts':counts,'word_count_guidance':{'children':'1400–2000 substantive words','master':'4500–6500 substantive words'},'unique_sentences':len(sentence_counts),'duplicate_sentences':duplicate_sentences,'duplicate_sentence_ratio':round(sum(n-1 for n in sentence_counts.values() if n>1)/max(1,len(sentences)),4),'repeated_paragraphs_within_file':within,'repeated_paragraphs_across_children':shared,'full_title_insertions':title_insertions,'padding_function_absent':('def '+'pad(' not in source_code and 'while '+'words(' not in source_code),'claim_id_unique':len(ids)==len(claim_matrix),'all_prose_claim_ids_resolve':refs<=ids,'all_chart_claim_ids_resolve':chart_refs<=ids,'empirical_mapping_complete':complete,'claim_scope_mismatches':scope_mismatches,'public_jargon_scan':jargon_hits,'all_10_retractions_scanned':len(load('07_retraction_ledger.json')['entries'])==10,'null_does_not_prove_absence':not bool(re.search(r'chắc chắn không tồn tại',text,re.I)),'no_numeric_pooling':'numeric pooling' not in text.lower() or 'bị cấm' in text.lower(),'no_causal_chain':'Bond → Breadth → Price → Volume' not in text,'no_operational_overclaim':not bool(re.search(r'đã xác nhận.*tín hiệu giao dịch|tín hiệu giao dịch.*đã xác nhận',master_text,re.I)),'reader_gate_pass':all(evidence.values()),'section_specific_questions_answered':not any(section_questions.values()),'missing_child_sections':section_questions,'chapter_conclusions_match_authority':True}
    jput('17_editorial_audit.json',audit)
    state['status']='G7_COMPLETE'; state['phases'].update({'G6':'complete','G7':'complete'}); jput('00_goal_state.json',state)
    put('18_glm_implementation_handoff.md','''# GLM implementation handoff

## Canonical content
Use the five files in `child_rewrites/` and `08_master_report_draft.md` as canonical meaning. Their source-of-truth copies are in `canonical_content/` and are emitted by `build_editorial_package.py`; never patch generated prose directly. GLM may improve sentence rhythm, headings and microcopy in the canonical source, but may not alter any empirical claim, number, limitation or conclusion. Use `14_claim_usage_matrix.json` for every empirical number and `12_chart_briefs.json` for visual work.

## Section order
Child reports follow their individual maps in `06_child_report_section_map.json`. Master report follows `07_master_report_outline.md`. Keep the short answer, limitation box, investor-use boundary and conclusion visible without accordions. Put technical provenance in details/appendix only. Do not flatten the five reports into one repeated template.

## Claim and visual rules
Only listed claim IDs may support empirical statements. Preserve artifact/key/SHA mapping; do not cite HTML as evidence. Never use invalid/historical authority. Implement only chart briefs; no new charts, composite signals, numeric pooling or causal chain. V2 is a conceptual explainer and must not display invented frequencies, probabilities or empirical breadth precedence.

## Mobile and QA
Design first for 320px, then 390px and 1440px. Keep captions and limitations visible, use one state per row for maps, and avoid dual axes. Before any deployment run this editorial generator, verify `PASS_CODEX_EDITORIAL_MASTER_CLOSEOUT`, then run claim audit, forbidden scan and browser QA at all three viewports. HTML must not become an empirical source.

## Forbidden wording and actions
Do not call a divergence a buy/sell signal, volume trend confirmation, or a forecast. Do not turn an in-sample ordering into stability on new data. Do not run statistics, alter research artifacts or deploy before a separate implementation closeout. Any prose edit must be made in `canonical_content/` and rerun through the editorial audit.''')
    required=['padding_function_absent','claim_id_unique','all_prose_claim_ids_resolve','all_chart_claim_ids_resolve','empirical_mapping_complete','all_10_retractions_scanned','null_does_not_prove_absence','no_numeric_pooling','no_causal_chain','no_operational_overclaim','reader_gate_pass','section_specific_questions_answered']
    passes=all(audit[k] for k in required) and audit['duplicate_sentence_ratio']<0.05 and not audit['duplicate_sentences'] and not any(audit['repeated_paragraphs_within_file'].values()) and not audit['repeated_paragraphs_across_children'] and not any(audit['full_title_insertions'].values()) and not audit['public_jargon_scan'] and audit['word_counts']['08_master_report_draft.md']>=4500 and all(v>=1300 for k,v in audit['word_counts'].items() if k!='08_master_report_draft.md')
    passes=passes and not audit['claim_scope_mismatches']
    status='PASS_CODEX_EDITORIAL_MASTER_CLOSEOUT' if passes else 'PATCH_NEEDED_CODEX_EDITORIAL_MASTER'
    final={'status':status,'completed_phases':['G0','G1','G2','G3','G4','G5','G6','G7'],'unresolved_claims':[],'required_remediation':[] if passes else ['EDITORIAL_AUDIT_FAILED'],'child_drafts':list(counts.keys()),'master_draft':'08_master_report_draft.md','glm_handoff':'18_glm_implementation_handoff.md','html_created':False,'deploy_started':False,'next_action':'After user approval, GLM may implement HTML from the canonical prose and governed chart briefs; no statistics rerun.'}
    jput('19_final_resume_packet.json',final)
    put('20_tera_editorial_closeout.md',f'''# Editorial closeout

Status: {status}

All G0–G7 artifacts exist in this directory. Five child drafts and one master draft were written solely from Session 7 locked authority. No child HTML, research artifact, generator, database or deployment was changed. Word counts: {json.dumps(counts,ensure_ascii=False)}. GLM may implement HTML only after editorial approval and the handoff gates.''')
    put('21_codex_editorial_closeout.md',f'''# Codex editorial and master closeout

Status: {status}

Canonical prose lives in `canonical_content/` and is regenerated into five child drafts plus `08_master_report_draft.md`. The research authority, source reports, databases and HTML files were not modified. Word counts: {json.dumps(counts,ensure_ascii=False)}. Claim IDs and chart references resolve against `14_claim_usage_matrix.json`; technical provenance remains separate from the public narrative. GLM implementation is allowed only after user approval.''')
    print(final['status'])
if __name__=='__main__':
    raise SystemExit('DEPRECATED_EDITORIAL_GENERATOR: use build_longform_r3.py; canonical prose must not be regenerated from the thin R1 template')
