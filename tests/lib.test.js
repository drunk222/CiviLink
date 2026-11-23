import test from 'node:test';
import assert from 'node:assert/strict';
import {formatYears} from '../lib.js';

test('BCE ranges keep the era marker on both ends',()=>{
 assert.equal(formatYears({start:-475,end:-220,dateLabel:'475 BC-221 BC'}),'公元前475—前220年');
 assert.equal(formatYears({start:-400,end:-301,dateLabel:'4th century BC'}),'公元前400—前301年');
 assert.equal(formatYears({start:-475,end:220,dateLabel:'跨公元'}),'公元前475—公元220年');
 assert.equal(formatYears({start:1500,end:1600,dateLabel:'1500-1600'}),'1500—1600年');
 assert.equal(formatYears({start:-400,end:-400,dateLabel:'约'}),'约公元前400年');
});
