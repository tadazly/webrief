import test from 'node:test';
import assert from 'node:assert/strict';
import { timeWindow, selectSessions, readMessages } from '../scripts/export-recent.mjs';

test('最近一天是滚动24小时，不是自然日', () => {
  assert.deepEqual(timeWindow(24, 2000000000000), { start: 1999913600, end: 2000000000 });
  assert.throws(() => timeWindow(NaN));
});
test('必须指定范围，同名会话要求唯一ID', () => {
  const sessions = [{ username: 'a@chatroom', displayName: '工作群' }, { username: 'b@chatroom', displayName: '工作群' }, { username: 'wxid_a', displayName: '朋友' }];
  assert.throws(() => selectSessions(sessions, {}));
  assert.throws(() => selectSessions(sessions, { chats: ['工作群'] }));
  assert.equal(selectSessions(sessions, { allGroups: true }).length, 2);
  assert.equal(selectSessions(sessions, { chats: ['a@chatroom'] })[0].username, 'a@chatroom');
});
test('分页取全、时间范围过滤、边界消息去重、按时间排序', async () => {
  const offsets = [];
  const pages = [
    { hasMore: true, messages: [{ serverId: '1', createTime: 100 }, { serverId: '2', createTime: 110 }] },
    { hasMore: false, messages: [{ serverId: '2', createTime: 110 }, { serverId: '3', createTime: 120 }, { serverId: '4', createTime: 121 }] }
  ];
  const result = await readMessages(async (_, params) => { offsets.push(params.offset); assert.equal(params.start, 100); assert.equal(params.end, 120); return pages.shift(); }, '群', { start: 100, end: 120 }, 2);
  assert.deepEqual(offsets, [0, 2]);
  assert.deepEqual(result.map(m => m.serverId), ['1', '2', '3']);
});
test('无法确认完整性时明确报错，不生成假完整报告', async () => {
  await assert.rejects(readMessages(async () => ({ messages: [], hasMore: true }), '群', { start: 1, end: 2 }), /空页/);
  await assert.rejects(readMessages(async () => ({ messages: [{ serverId: '1', createTime: 1 }], hasMore: true }), '群', { start: 1, end: 2 }), /重复/);
});
